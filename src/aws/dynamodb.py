import abc
import json
import threading
import time
from typing import Any, Callable, Tuple, Union, Optional, List, Mapping, Dict, Collection, Iterable

from aws import is_not_found_exception, is_exception
from utils import date_utils, exception_utils


class KeySchema:
    def __init__(self, node: dict):
        self.attribute_name = node['AttributeName']
        self.key_type = node['KeyType']


class AttributeDefinition:
    def __init__(self, node: dict):
        self.name = node['AttributeName']
        self.type = node['AttributeType']


class ProvisionedThroughput:
    def __init__(self, node: dict):
        self.last_decreased_time = node.get('LastDecreaseDateTime')
        self.read_capacity_units = node['ReadCapacityUnits']
        self.write_capacity_units = node['WriteCapacityUnits']


class PrimaryKeyViolationException(Exception):
    def __init__(self):
        super(PrimaryKeyViolationException, self).__init__("Primary key violation")


class PreconditionFailedException(Exception):
    def __init__(self):
        super(PreconditionFailedException, self).__init__("Precondition Failed")


class ResourceNotFoundException(Exception):
    def __init__(self):
        super(ResourceNotFoundException, self).__init__("Resource not found")


class ClientError(Exception):
    def __init__(self, ex: Any):
        super(ClientError, self).__init__(exception_utils.get_exception_message(ex))
        self.error_code = ex.response['Error']['Code']


class ThrottlingException(Exception):
    def __init__(self, ex: Any):
        super(Exception, self).__init__(exception_utils.get_exception_message(ex))


class DynamoDbValidationException(Exception):
    def __init__(self, message: str):
        super(DynamoDbValidationException, self).__init__(message)


class CancelReason:
    def __init__(self, node: dict):
        self.code = node['Code']
        if self.code == 'None':
            self.code = None
        self.message = node.get('Message')


class TransactionCancelledException(Exception):
    def __init__(self, nodes: List[Dict[str, Any]]):
        super(TransactionCancelledException, self).__init__("TransactionCancelled")
        self.reasons = list(map(CancelReason, nodes))


def _from_ddb_item(item: dict) -> dict:
    def convert_value(value: dict):
        keys = list(value.keys())
        if len(keys) > 1:
            raise ValueError("Too many keys")
        att_type = keys[0]
        att_value = value[keys[0]]

        if att_type == "S" or att_type == "BOOL" or att_type == "B":
            return att_value
        if att_type == "N":
            if "." in att_value:
                return float(att_value)
            return int(att_value)
        if att_type == "M":
            return build_map(att_value)
        if att_type == "L":
            values = []
            for x in att_value:
                values.append(convert_value(x))
            return values
        if att_type == "NULL":
            return None
        raise ValueError(f"Don't know how to handle {att_type}")

    def build_map(entry: dict) -> dict:
        new_record = {}
        for key, value in entry.items():
            new_record[key] = convert_value(value)
        return new_record

    return build_map(item)


def _to_attribute_value_map(entry: dict) -> dict:
    new_record = {}
    for key, value in entry.items():
        at, av = _to_attribute_value(value)
        new_record[key] = {at: av}
    return new_record


def _to_attribute_value(value: Any):
    if value is None:
        return "NULL", True
    t = type(value)
    if t is int or t is float:
        attribute_type = "N"
        attribute_value = str(value)
    elif t is str:
        attribute_type = "S"
        attribute_value = value
    elif t is bool:
        attribute_type = "BOOL"
        attribute_value = value
    elif t is list:
        attribute_type = "L"
        arr = []
        for x in value:
            t, v = _to_attribute_value(x)
            arr.append({t: v})
        attribute_value = arr
    elif t is dict:
        attribute_type = "M"
        attribute_value = _to_attribute_value_map(value)
    elif t is bytes:
        attribute_type = "B"
        attribute_value = value
    else:
        raise Exception(f"Don't know how to handle {t}")
    return attribute_type, attribute_value


def _to_ddb_item(entry: dict) -> dict:
    return _to_attribute_value_map(entry)


def _handle_client_error(ex):
    code = ex.response['Error']['Code']
    if code == "ValidationException":
        raise DynamoDbValidationException(exception_utils.get_exception_message(ex))
    if code == "ThrottlingException":
        raise ThrottlingException(ex)
    raise ClientError(ex)


def _handle_exception(ex: Exception):
    if is_not_found_exception(ex):
        raise ResourceNotFoundException()

    if is_exception(ex, 400, "TransactionCanceledException"):
        raise TransactionCancelledException(ex.response['CancellationReasons'])

    type_string = str(type(ex))
    if "ConditionalCheckFailedException" in type_string:
        raise PreconditionFailedException()

    if type_string.find("ResourceNotFoundException") > -1:
        raise ResourceNotFoundException()

    if type_string.find("ClientError") > -1:
        _handle_client_error(ex)

    print(f"!!! Don't know how to handle {type_string}: {json.dumps(ex.__dict__, indent=True)}")
    raise ex


def _process_condition(condition: Union[dict, Tuple[str, dict]], params: dict):
    if type(condition) is tuple:
        bind_vars = _to_ddb_item(condition[1])
        statement = condition[0]
    else:
        counter = 1
        expr = ""
        bind_vars = {}
        for key, value in _to_ddb_item(condition).items():
            if counter > 1:
                expr += " AND "
            bind_name = f":c{counter}"
            expr += f"{key} = {bind_name}"
            bind_vars[bind_name] = value
            counter += 1
        statement = expr
    params['ConditionExpression'] = statement
    params['ExpressionAttributeValues'] = bind_vars


def _merge_key_condition(keys: Iterable[str], params: dict):
    statement = params.pop('ConditionExpression', "")

    for key in keys:
        if len(statement) > 0:
            statement += " AND "
        statement += f"attribute_exists({key})"
    params['ConditionExpression'] = statement


def _merge_attributes(params: dict, attributes: dict):
    existing = params.get('ExpressionAttributeValues')
    if existing is None:
        existing = {}
        params['ExpressionAttributeValues'] = existing
    for key, value in attributes.items():
        existing[key] = value


class DynamoResponse:
    def __init__(self, start_time: int, response: Mapping, throttle_count: int):
        self.start_time = start_time
        self.elapsed_time = date_utils.get_system_time_in_millis() - start_time
        self.throttle_count = throttle_count
        if response is not None:
            cc = response.get('ConsumedCapacity')
            self.capacity_units = cc.get('CapacityUnits') if cc is not None else None
            self.retry_attempts = response.get('RetryAttempts', 0)
        else:
            self.capacity_units = self.retry_attempts = 0


class TransactionRequest(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def to_ddb_request(self) -> Dict[str, Any]:
        raise NotImplementedError()


class PutItemRequest(TransactionRequest):
    def __init__(self,
                 table_name: str,
                 item: Dict[str, Any],
                 key_attributes: Optional[List[str]] = None,
                 condition: Union[dict, Tuple[str, dict]] = None
                 ):
        self.table_name = table_name
        self.item = item
        self.key_attributes = key_attributes
        self.condition = condition

    def to_ddb_request(self) -> Dict[str, Any]:
        ddb_item = _to_ddb_item(self.item)
        params = {
            "TableName": self.table_name,
            "Item": ddb_item
        }
        if self.key_attributes is not None and len(self.key_attributes) > 0:
            assert self.condition is None
            expr = ""
            for att in self.key_attributes:
                if len(expr) > 0:
                    expr += " AND "
                expr += f"attribute_not_exists({att})"
            params['ConditionExpression'] = expr

        if self.condition is not None:
            _process_condition(self.condition, params)

        return {'Put': params}


class UpdateItemRequest(TransactionRequest):
    def __init__(self,
                 table_name: str,
                 keys: dict,
                 item: Dict[str, Any],
                 condition: Union[dict, Tuple[str, dict]] = None
                 ):
        self.table_name = table_name
        self.item = item
        self.keys = keys
        self.condition = condition

    def to_ddb_request(self) -> Dict[str, Any]:
        ddb_item = _to_ddb_item(self.item)
        ddb_key = _to_ddb_item(self.keys)
        update_expression = None
        expression_values = {}
        counter = 1
        for key, value in ddb_item.items():
            if key in self.keys:
                continue
            if update_expression is None:
                update_expression = "SET "
            else:
                update_expression += ", "
            bind_name = f":v{counter}"
            counter += 1
            update_expression += f"{key} = {bind_name}"
            expression_values[bind_name] = value

        params = {
            "TableName": self.table_name,
            "Key": ddb_key,
            "UpdateExpression": update_expression
        }
        if self.condition is not None:
            _process_condition(self.condition, params)

        _merge_key_condition(self.keys.keys(), params)

        _merge_attributes(params, expression_values)

        return {'Update': params}


class DeleteItemRequest(TransactionRequest):
    def __init__(self,
                 table_name: str,
                 keys: dict,
                 condition: Union[dict, Tuple[str, dict]] = None
                 ):
        self.table_name = table_name
        self.keys = keys
        self.condition = condition

    def to_ddb_request(self) -> Dict[str, Any]:
        ddb_key = _to_ddb_item(self.keys)
        params = {
            "TableName": self.table_name,
            "Key": ddb_key
        }
        if self.condition is None:
            expr = ""
            for att in self.keys.keys():
                if len(expr) > 0:
                    expr += " AND "
                expr += f"attribute_exists({att})"
            params['ConditionExpression'] = expr

        if self.condition is not None:
            _process_condition(self.condition, params)
        return {'Delete': params}


class DynamoDb:
    def __init__(self, client):
        self.__client = client
        self.__thread_local = threading.local()

    def get_last_response(self) -> Union[DynamoResponse, None]:
        if hasattr(self.__thread_local, 'last_response'):
            return self.__thread_local.last_response
        return None

    def _handle_throttling(self, function_to_call) -> Any:
        self.__thread_local.throttle_count = 0
        while True:
            try:
                try:
                    return function_to_call()
                except Exception as ex:
                    _handle_exception(ex)
                    return None
            except ThrottlingException:
                self.__thread_local.throttle_count += 1
                time.sleep(1)

    def _execute_and_wrap(self, function_to_call: Callable):
        start = date_utils.get_system_time_in_millis()
        resp = self._handle_throttling(function_to_call)
        if resp is not None:
            self.__thread_local.last_response = DynamoResponse(start, resp, self.__thread_local.throttle_count)
        return resp

    def find_item(self, table_name: str, keys: dict, consistent: bool = False):
        try:
            return self.get_item(table_name, keys, consistent)
        except ResourceNotFoundException:
            return None

    def get_item(self, table_name: str, keys: dict, consistent: bool = False):
        ddb_keys = _to_ddb_item(keys)
        params = {"TableName": table_name,
                  "Key": ddb_keys}

        if consistent:
            params['ConsistentRead'] = True

        record = self._execute_and_wrap(lambda: self.__client.get_item(**params))
        item = record.get('Item')
        if item is None:
            return None
        return _from_ddb_item(item)

    def put_item(self, table_name: str,
                 item: dict,
                 key_attributes: Optional[Collection[str]] = None,
                 condition: Union[dict, Tuple[str, dict]] = None):
        ddb_item = _to_ddb_item(item)
        params = {"TableName": table_name,
                  "Item": ddb_item,
                  "ReturnConsumedCapacity": "TOTAL",
                  "ReturnItemCollectionMetrics": "SIZE"}
        if key_attributes is not None and len(key_attributes) > 0:
            assert condition is None
            expr = ""
            for att in key_attributes:
                if len(expr) > 0:
                    expr += " AND "
                expr += f"attribute_not_exists({att})"
            params['ConditionExpression'] = expr

        if condition is not None:
            _process_condition(condition, params)

        try:
            return self._execute_and_wrap(lambda: self.__client.put_item(**params))
        except PreconditionFailedException as ex:
            if condition is None:
                raise PrimaryKeyViolationException()
            raise ex

    def delete_item(self, table_name: str,
                    keys: dict,
                    condition: Union[dict, Tuple[str, dict]] = None) -> bool:
        params = {"TableName": table_name,
                  "Key": _to_ddb_item(keys),
                  "ReturnValues": "ALL_OLD"}
        if condition is not None:
            _process_condition(condition, params)
        resp = self._execute_and_wrap(lambda: self.__client.delete_item(**params))
        return resp.get('Attributes') is not None

    def delete_items(self, table_name: str,
                     keys: List[Dict[str, Any]]):
        items = []
        req = {table_name: items}
        for key in keys:
            item = {
                'DeleteRequest': {
                    'Key': _to_ddb_item(key)
                }
            }
            items.append(item)
        self._execute_and_wrap(lambda: self.__client.batch_write_item(RequestItems=req))

    def update_item(self, table_name: str,
                    keys: dict,
                    item: dict,
                    condition: Union[dict, Tuple[str, dict]] = None):
        ddb_item = _to_ddb_item(item)
        update_expression = None
        expression_values = {}
        counter = 1
        for key, value in ddb_item.items():
            if key in keys:
                continue
            if update_expression is None:
                update_expression = "SET "
            else:
                update_expression += ", "
            bind_name = f":v{counter}"
            counter += 1
            update_expression += f"{key} = {bind_name}"
            expression_values[bind_name] = value

        params = {"TableName": table_name,
                  "ReturnConsumedCapacity": "TOTAL",
                  "ReturnItemCollectionMetrics": "SIZE",
                  "Key": _to_ddb_item(keys),
                  "UpdateExpression": update_expression}

        if condition is not None:
            _process_condition(condition, params)

        _merge_key_condition(keys.keys(), params)

        _merge_attributes(params, expression_values)

        resp = self._execute_and_wrap(lambda: self.__client.update_item(**params))
        return resp

    def transact_write(self, items: List[TransactionRequest]):
        item_list = list(map(lambda item: item.to_ddb_request(), items))
        return self._execute_and_wrap(lambda: self.__client.transact_write_items(TransactItems=item_list))
