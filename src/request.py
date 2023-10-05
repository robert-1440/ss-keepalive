import json
import sys
from typing import Dict, Any, Type, Union, Optional

from utils.loghelper import get_logger

logger = get_logger(__name__)


class HttpRequest:
    headers: dict[str, Any]
    method: str
    source_ip: str
    path: str
    __body_record: Optional[Dict[str, Any]]

    def __init__(self, event: Dict[str, Any]):
        if "rawPath" in event:
            self.path = event['rawPath']
            request_context = get_or_not_found(event, "requestContext", dict)
            http = get_or_not_found(request_context, "http", dict)
            self.source_ip = get_or_not_found(http, "sourceIp", str)
            self.method = get_or_not_found(http, "method", str)
            self.headers = get_required_parameter(event, "headers", dict)
        else:
            self.path = get_or_not_found(event, 'path', str)
            self.method = get_or_not_found(event, "httpMethod", str)
            request_context = get_or_not_found(event, "requestContext", dict)
            self.path = request_context.get('path', self.path)
            identity = get_or_not_found(request_context, "identity", dict)
            self.source_ip = get_or_not_found(identity, "sourceIp", str)
            headers = get_required_parameter(event, "headers", dict)
            self.headers = {}
            for key, value in headers.items():
                self.headers[key.lower()] = value

        self.body: Optional[str] = event.get('body')
        self.__body_record = None
        self.query_string_parameters: Optional[Dict[str, str]] = event.get('queryStringParameters')

        self.__attributes = {}

    def assert_empty_body(self):
        if self.has_body():
            raise BadRequestException("Expected an empty body.")

    def has_body(self):
        return self.body is not None and len(self.body) > 0

    def get_body_record(self) -> Dict[str, Any]:
        if self.__body_record is None:
            self.__body_record = json.loads(self.body)
        return self.__body_record

    def get_required_body_record(self) -> Dict[str, Any]:
        return json.loads(self.get_required_body())

    def dump_headers(self) -> str:
        return json.dumps(self.headers, indent=True)

    def find_header(self, name: str):
        return self.headers.get(name)

    def get_required_header(self, name: str):
        return get_required_header(self.headers, name)

    def get_header(self, name: str) -> Optional[str]:
        return self.headers.get(name)

    def get_required_body(self) -> str:
        if self.body is None or len(self.body) == 0:
            logger.warning(f"Received empty body for {self.path}.")
            raise BadRequestException("Empty body not allowed")
        return self.body

    def get_attribute(self, key: str) -> Optional[Any]:
        return self.__attributes.get(key)

    def set_attribute(self, key: str, value: Any):
        self.__attributes[key] = value

    def invoke_attribute_as_function(self, key: str, *args) -> Any:
        v = self.__attributes.get(key)
        assert callable(v)
        return v(*args)


class HttpException(Exception):
    def __init__(self, code: int, message: str):
        super(HttpException, self).__init__(message)
        self.code = code
        self.message = message

    def to_response(self) -> Dict[str, Any]:
        return {"statusCode": self.code,
                "body": {"errorMessage": self.message}
                }


class ForbiddenException(HttpException):
    def __init__(self, message: str):
        super(ForbiddenException, self).__init__(403, f"Forbidden: {message}")


class NotAuthorizedException(HttpException):
    def __init__(self, message: str):
        super(NotAuthorizedException, self).__init__(401, f"Not Authorized: {message}")


class NotFoundException(HttpException):
    def __init__(self, resource: str = None):
        message = "Resource Not Found"
        if resource is not None and len(resource) > 0:
            message += f": {resource}"
        super(NotFoundException, self).__init__(404, message)


class GoneException(HttpException):
    def __init__(self, message: str = None):
        super(GoneException, self).__init__(410, message)


class MethodNotAllowedException(HttpException):
    def __init__(self):
        super(MethodNotAllowedException, self).__init__(415, "Method not allowed")


class BadRequestException(HttpException):
    def __init__(self, message: str):
        super(BadRequestException, self).__init__(400, message)


class ConflictException(HttpException):
    def __init__(self, message: str):
        super(ConflictException, self).__init__(409, message)


class EntityExistsException(HttpException):
    def __init__(self, message: str):
        super(EntityExistsException, self).__init__(409, message)


class MissingParameterException(BadRequestException):
    def __init__(self, parameter: str, parameter_type: str = "parameter"):
        super(MissingParameterException, self).__init__(f"Missing {parameter_type} '{parameter}'.")


class InvalidParameterException(BadRequestException):
    def __init__(self, parameter: str, message: str):
        super(InvalidParameterException, self).__init__(f"'{parameter}' is invalid: {message}")


def get_or_not_found(event: Dict[str, Any],
                     parameter_name: str,
                     expected_type: Type):
    try:
        return get_required_parameter(event, parameter_name, expected_type)
    except Exception as ex:
        print(f"Error extracting '{parameter_name}': {ex}", file=sys.stderr)
        raise NotFoundException()


def get_or_auth_fail(event: Dict[str, Any],
                     parameter_name: str,
                     expected_type: Type,
                     parameter_type: str = "parameter"):
    try:
        return get_required_parameter(event, parameter_name, expected_type,
                                      parameter_type=parameter_type)
    except Exception as ex:
        raise NotAuthorizedException(f"{ex}")


__NULL = object()


def assert_empty(event: Dict[str, Any]):
    if len(event) != 0:
        raise BadRequestException(f"The following properties are not recognized: {','.join(event.keys())}.")


def get_parameter(event: Dict[str, Any],
                  parameter_name: str,
                  expected_type: Type,
                  remove: bool = False,
                  none_if_empty: bool = False,
                  none_ok: bool = True) -> Any:
    v = event.get(parameter_name, __NULL) if not remove else event.pop(parameter_name, __NULL)
    if id(v) == id(__NULL):
        return None
    if v is None:
        if not none_ok:
            raise InvalidParameterException(parameter_name, "parameter cannot be null.")
        return None
    if expected_type is Any:
        return v
    t = type(v)
    if t is not expected_type:
        raise InvalidParameterException(parameter_name, "invalid type.")
    if t is str:
        if none_if_empty:
            v = v.strip()
            if len(v) == 0:
                if not none_ok:
                    raise InvalidParameterException(parameter_name, "value cannot be empty.")
                v = None
    return v


def get_required_header(event: Dict[str, Any],
                        header_name: str):
    return get_required_parameter(event, header_name, str, parameter_type="header")


def get_required_parameter(event: Dict[str, Any],
                           parameter_name: str,
                           expected_type: Type,
                           parameter_type: str = "parameter",
                           remove: bool = False,
                           empty_ok: bool = False) -> Any:
    v = get_parameter(event, parameter_name, expected_type, remove=remove)
    if v is None:
        raise MissingParameterException(parameter_name, parameter_type=parameter_type)
    if not empty_ok and expected_type == str and len(v) == 0:
        raise BadRequestException(f"'{parameter_name}' cannot be empty")
    return v


def from_json(data: Union[dict, str]) -> Dict[str, Any]:
    if type(data) is dict:
        return data
    try:
        return json.loads(data)
    except Exception:
        raise BadRequestException("Malformed JSON")


class Response:
    def __init__(self, code: int, body: Any = None):
        self.code = code
        self.body = body

    def to_dict(self) -> Dict[str, Any]:
        record = {'statusCode': self.code}
        if self.body is not None:
            record['body'] = self.body
        return record

    @classmethod
    def ok(cls, body: Any = None):
        return Response(200, body)

    @classmethod
    def no_content(cls):
        return Response(204)

    @classmethod
    def created(cls, body: Any):
        return Response(201, body)


class ParameterCollector:

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def apply_to(self, target: Union[dict, Any], include_nulls: bool = False):
        if not isinstance(target, dict):
            target = target.__dict__

        for key, value in self.__dict__.items():
            if include_nulls or value is not None:
                target[key] = value

    def to_dict(self):
        return dict(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def prune(self):
        """
        Removes all keys that have values of None.
        """
        for key in list(self.__dict__.keys()):
            v = self.__dict__[key]
            if v is None:
                del self.__dict__[key]

    def assert_not_empty(self, strip_none: bool = True):
        if self.is_empty(strip_none=strip_none):
            raise BadRequestException(f"Empty body.")

    def is_empty(self, strip_none: bool = True) -> bool:
        if len(self) == 0:
            return True
        if not strip_none:
            return False
        for _ in filter(lambda v: v is not None, self.__dict__.values()):
            return False
        return True


def to_int(value: str, parameter_name: str) -> int:
    try:
        return int(value)
    except Exception:
        raise BadRequestException(f"{parameter_name}: '{value}' is not a valid integer.")
