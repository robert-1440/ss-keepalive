import abc
from copy import deepcopy
from typing import List, Optional, Any, Dict, Tuple, Iterable, Callable

from aws.dynamodb import DynamoDbValidationException
from botomocks import AwsResourceNotFoundResponseException, assert_empty, AwsInvalidRequestResponseException, \
    raise_invalid_parameter
from botomocks.exceptions import ConditionalCheckFailedException, AwsExceptionResponseException, \
    AwsTransactionCanceledException

RESERVED_WORDS = {
    "abort",
    "absolute",
    "action",
    "add",
    "after",
    "agent",
    "aggregate",
    "all",
    "allocate",
    "alter",
    "analyze",
    "and",
    "any",
    "archive",
    "are",
    "array",
    "as",
    "asc",
    "ascii",
    "asensitive",
    "assertion",
    "asymmetric",
    "at",
    "atomic",
    "attach",
    "attribute",
    "auth",
    "authorization",
    "authorize",
    "auto",
    "avg",
    "back",
    "backup",
    "base",
    "batch",
    "before",
    "begin",
    "between",
    "bigint",
    "binary",
    "bit",
    "blob",
    "block",
    "boolean",
    "both",
    "breadth",
    "bucket",
    "bulk",
    "by",
    "byte",
    "call",
    "called",
    "calling",
    "capacity",
    "cascade",
    "cascaded",
    "case",
    "cast",
    "catalog",
    "char",
    "character",
    "check",
    "class",
    "clob",
    "close",
    "cluster",
    "clustered",
    "clustering",
    "clusters",
    "coalesce",
    "collate",
    "collation",
    "collection",
    "column",
    "columns",
    "combine",
    "comment",
    "commit",
    "compact",
    "compile",
    "compress",
    "condition",
    "conflict",
    "connect",
    "connection",
    "consistency",
    "consistent",
    "constraint",
    "constraints",
    "constructor",
    "consumed",
    "continue",
    "convert",
    "copy",
    "corresponding",
    "count",
    "counter",
    "create",
    "cross",
    "cube",
    "current",
    "cursor",
    "cycle",
    "data",
    "database",
    "date",
    "datetime",
    "day",
    "deallocate",
    "dec",
    "decimal",
    "declare",
    "default",
    "deferrable",
    "deferred",
    "define",
    "defined",
    "definition",
    "delete",
    "delimited",
    "depth",
    "deref",
    "desc",
    "describe",
    "descriptor",
    "detach",
    "deterministic",
    "diagnostics",
    "directories",
    "disable",
    "disconnect",
    "distinct",
    "distribute",
    "do",
    "domain",
    "double",
    "drop",
    "dump",
    "duration",
    "dynamic",
    "each",
    "element",
    "else",
    "elseif",
    "empty",
    "enable",
    "end",
    "equal",
    "equals",
    "error",
    "escape",
    "escaped",
    "eval",
    "evaluate",
    "exceeded",
    "except",
    "exception",
    "exceptions",
    "exclusive",
    "exec",
    "execute",
    "exists",
    "exit",
    "explain",
    "explode",
    "export",
    "expression",
    "extended",
    "external",
    "extract",
    "fail",
    "false",
    "family",
    "fetch",
    "fields",
    "file",
    "filter",
    "filtering",
    "final",
    "finish",
    "first",
    "fixed",
    "flattern",
    "float",
    "for",
    "force",
    "foreign",
    "format",
    "forward",
    "found",
    "free",
    "from",
    "full",
    "function",
    "functions",
    "general",
    "generate",
    "get",
    "glob",
    "global",
    "go",
    "goto",
    "grant",
    "greater",
    "group",
    "grouping",
    "handler",
    "hash",
    "have",
    "having",
    "heap",
    "hidden",
    "hold",
    "hour",
    "identified",
    "identity",
    "if",
    "ignore",
    "immediate",
    "import",
    "in",
    "including",
    "inclusive",
    "increment",
    "incremental",
    "index",
    "indexed",
    "indexes",
    "indicator",
    "infinite",
    "initially",
    "inline",
    "inner",
    "innter",
    "inout",
    "input",
    "insensitive",
    "insert",
    "instead",
    "int",
    "integer",
    "intersect",
    "interval",
    "into",
    "invalidate",
    "is",
    "isolation",
    "item",
    "items",
    "iterate",
    "join",
    "key",
    "keys",
    "lag",
    "language",
    "large",
    "last",
    "lateral",
    "lead",
    "leading",
    "leave",
    "left",
    "length",
    "less",
    "level",
    "like",
    "limit",
    "limited",
    "lines",
    "list",
    "load",
    "local",
    "localtime",
    "localtimestamp",
    "location",
    "locator",
    "lock",
    "locks",
    "log",
    "loged",
    "long",
    "loop",
    "lower",
    "map",
    "match",
    "materialized",
    "max",
    "maxlen",
    "member",
    "merge",
    "method",
    "metrics",
    "min",
    "minus",
    "minute",
    "missing",
    "mod",
    "mode",
    "modifies",
    "modify",
    "module",
    "month",
    "multi",
    "multiset",
    "name",
    "names",
    "national",
    "natural",
    "nchar",
    "nclob",
    "new",
    "next",
    "no",
    "none",
    "not",
    "null",
    "nullif",
    "number",
    "numeric",
    "object",
    "of",
    "offline",
    "offset",
    "old",
    "on",
    "online",
    "only",
    "opaque",
    "open",
    "operator",
    "option",
    "or",
    "order",
    "ordinality",
    "other",
    "others",
    "out",
    "outer",
    "output",
    "over",
    "overlaps",
    "override",
    "owner",
    "pad",
    "parallel",
    "parameter",
    "parameters",
    "partial",
    "partition",
    "partitioned",
    "partitions",
    "path",
    "percent",
    "percentile",
    "permission",
    "permissions",
    "pipe",
    "pipelined",
    "plan",
    "pool",
    "position",
    "precision",
    "prepare",
    "preserve",
    "primary",
    "prior",
    "private",
    "privileges",
    "procedure",
    "processed",
    "project",
    "projection",
    "property",
    "provisioning",
    "public",
    "put",
    "query",
    "quit",
    "quorum",
    "raise",
    "random",
    "range",
    "rank",
    "raw",
    "read",
    "reads",
    "real",
    "rebuild",
    "record",
    "recursive",
    "reduce",
    "ref",
    "reference",
    "references",
    "referencing",
    "regexp",
    "region",
    "reindex",
    "relative",
    "release",
    "remainder",
    "rename",
    "repeat",
    "replace",
    "request",
    "reset",
    "resignal",
    "resource",
    "response",
    "restore",
    "restrict",
    "result",
    "return",
    "returning",
    "returns",
    "reverse",
    "revoke",
    "right",
    "role",
    "roles",
    "rollback",
    "rollup",
    "routine",
    "row",
    "rows",
    "rule",
    "rules",
    "sample",
    "satisfies",
    "save",
    "savepoint",
    "scan",
    "schema",
    "scope",
    "scroll",
    "search",
    "second",
    "section",
    "segment",
    "segments",
    "select",
    "self",
    "semi",
    "sensitive",
    "separate",
    "sequence",
    "serializable",
    "session",
    "set",
    "sets",
    "shard",
    "share",
    "shared",
    "short",
    "show",
    "signal",
    "similar",
    "size",
    "skewed",
    "smallint",
    "snapshot",
    "some",
    "source",
    "space",
    "spaces",
    "sparse",
    "specific",
    "specifictype",
    "split",
    "sql",
    "sqlcode",
    "sqlerror",
    "sqlexception",
    "sqlstate",
    "sqlwarning",
    "start",
    "state",
    "static",
    "status",
    "storage",
    "store",
    "stored",
    "stream",
    "string",
    "struct",
    "style",
    "sub",
    "submultiset",
    "subpartition",
    "substring",
    "subtype",
    "sum",
    "super",
    "symmetric",
    "synonym",
    "system",
    "table",
    "tablesample",
    "temp",
    "temporary",
    "terminated",
    "text",
    "than",
    "then",
    "throughput",
    "time",
    "timestamp",
    "timezone",
    "tinyint",
    "to",
    "token",
    "total",
    "touch",
    "trailing",
    "transaction",
    "transform",
    "translate",
    "translation",
    "treat",
    "trigger",
    "trim",
    "true",
    "truncate",
    "ttl",
    "tuple",
    "type",
    "under",
    "undo",
    "union",
    "unique",
    "unit",
    "unknown",
    "unlogged",
    "unnest",
    "unprocessed",
    "unsigned",
    "until",
    "update",
    "upper",
    "url",
    "usage",
    "use",
    "user",
    "users",
    "using",
    "uuid",
    "vacuum",
    "value",
    "valued",
    "values",
    "varchar",
    "variable",
    "variance",
    "varint",
    "varying",
    "view",
    "views",
    "virtual",
    "void",
    "wait",
    "when",
    "whenever",
    "where",
    "while",
    "window",
    "with",
    "within",
    "without",
    "work",
    "wrapped",
    "write",
    "year",
    "zone"
}


class KeyPart:
    def __init__(self, attribute_name: str, attribute_type: str):
        self.attribute_name = attribute_name
        self.attribute_type = attribute_type


class KeyDefinition:
    def __init__(self, parts: List[KeyPart]):
        self.parts = parts

    def build_key(self, row: Dict[str, Dict[str, Any]]):
        key = ""
        for part in self.parts:
            v = row[part.attribute_name]
            if len(key) > 0:
                key += "^"
            key += str(_get_attribute_value(v))
        return key


class AttributeValue:
    def __init__(self, attribute_type: str, attribute_value: Any):
        self.attribute_type = attribute_type
        self.attribute_value = attribute_value

    def to_dict(self):
        return {self.attribute_type: self.attribute_value}


def _get_attribute_value(value: Dict[str, Any]):
    keys = list(value.keys())
    if len(keys) > 1:
        raise ValueError("Too many keys")
    return value[keys[0]]


class Table:
    def __init__(self, name: str,
                 hash_key: KeyDefinition,
                 range_key: Optional[KeyDefinition]):
        self.hash_key = hash_key
        self.range_key = range_key
        self.name = name
        self.rows: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def __build_key(self, row: Dict[str, Dict[str, Any]]):
        key = self.hash_key.build_key(row)
        if self.range_key is not None:
            key += f'\t{self.range_key.build_key(row)}'

        return key

    def find_by_example(self, row: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Dict[str, Any]]]:
        key = self.__build_key(row)
        return self.rows.get(key)

    def add(self, row: Dict[str, Dict[str, Any]], replace: bool = True):
        key = self.__build_key(row)
        if not replace:
            if key in self.rows:
                raise ConditionalCheckFailedException("PutItem")
        self.rows[key] = row

    def get(self, key: Dict[str, Dict[str, Any]]):
        our_key = self.__build_key(key)
        v = self.rows.get(our_key)
        return v

    def remove(self, key: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        our_key = self.__build_key(key)
        return self.rows.pop(our_key, None)

    def query(self, partition_key: Dict[str, Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        our_key = self.hash_key.build_key(partition_key) + '\t'
        return map(lambda kr: kr[1], filter(lambda kr: kr[0].startswith(our_key), self.rows.items()))


class Condition(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def check(self, record: Dict[str, Any], attributes: Dict[str, Any]) -> bool:
        raise NotImplementedError()


class EqualCondition(Condition):
    def __init__(self, name: str, bind_name: str):
        self.name = name
        self.bind_name = bind_name

    def check(self, record: Dict[str, Any], attributes: Dict[str, Any]):
        value = attributes[self.bind_name]
        return record.get(self.name) == value


class AttributeExistsCondition(Condition):
    def __init__(self, name: str):
        self.name = name

    def check(self, record: Dict[str, Any], attributes: Dict[str, Any]):
        return record.get(self.name) is not None


class AttributeDoesNotExistCondition(Condition):
    def __init__(self, name: str):
        self.name = name

    def check(self, record: Dict[str, Any], attributes: Dict[str, Any]):
        return record.get(self.name) is None


class Conditions:
    def __init__(self, conditions: List[Condition]):
        self.conditions = conditions

    def validate(self, operation: str, record: dict, attributes: dict):
        for c in self.conditions:
            if not c.check(record, attributes):
                raise ConditionalCheckFailedException(operation)


def _parse_conditions(expr: str) -> Conditions:
    values = expr.split(" AND ")
    condition_list = []
    for v in values:
        parsed = _parse_condition_expression(v)
        if parsed.right is not None:
            if parsed.operation == '=':
                condition_list.append(EqualCondition(parsed.left, parsed.right))
            else:
                raise NotImplementedError(f"{parsed.operation} not supported.")
        elif parsed.operation == "attribute_exists":
            condition_list.append(AttributeExistsCondition(parsed.left))
        elif parsed.operation == "attribute_not_exists":
            condition_list.append(AttributeDoesNotExistCondition(parsed.left))
        else:
            raise NotImplementedError(f"Can't parsed {expr}")
    assert len(condition_list) > 0
    return Conditions(condition_list)


def _extract_assignment(expr: str, attributes: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    kv_pair = expr.split(" = ")
    prop_name = kv_pair[0].strip()
    bind_name = kv_pair[1].strip()
    return prop_name, attributes[bind_name]


def _collect_updates(expr: str, attributes: Dict[str, Dict[str, Any]]):
    if not expr.startswith("SET "):
        raise NotImplementedError(f"Unsupported expression: {expr}")
    values = expr[3::].split(",")
    record = {}
    for v in values:
        kv_pair = v.split(" = ")
        prop_name = kv_pair[0].strip()
        check_keyword(prop_name)
        bind_name = kv_pair[1].strip()
        record[prop_name] = attributes[bind_name]
    return record


def check_keyword(attribute: str):
    if attribute.lower() in RESERVED_WORDS:
        raise DynamoDbValidationException(
            f'Invalid expression: Attribute name is a reserved keyword; reserved keyword: {attribute}')


class ParsedExpression:
    def __init__(self, action: str, attribute: str):
        check_keyword(attribute)
        self.action = action
        self.attribute = attribute


def _parse_expression(expr: str) -> ParsedExpression:
    index = expr.index('(')
    if index > 0:
        end_index = expr.index(')', index + 1)
        if end_index > 0:
            action = expr[0:index:]
            attribute = expr[index + 1:end_index:]
            return ParsedExpression(action, attribute)
    raise AssertionError(f"Cannot parse expression {expr}")


class ParsedConditionExpression:
    def __init__(self, left: str, operation: str, right: Optional[str]):
        check_keyword(left)
        self.left = left
        self.operation = operation
        self.right = right


def _parse_condition_expression(expr: str) -> ParsedConditionExpression:
    values = expr.split(' ')
    if len(values) == 3:
        return ParsedConditionExpression(values[0].strip(), values[1].strip(), values[2].strip())
    elif len(values) == 1:
        v = values[0]
        index = v.find('(')
        if index > 0:
            end_index = v.find(')')
            if end_index > 0:
                operation = v[0:index:]
                attribute = v[index + 1:end_index:]
                return ParsedConditionExpression(attribute, operation, None)
    raise AssertionError(f"Can't parse '{expr}'")


class MockDynamoDbClient:
    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self.update_count = 0
        self.__update_callback: Optional[Callable] = None
        self.__delete_callback: Optional[Callable] = None

    def set_update_callback(self, callback: Optional[Callable]):
        self.__update_callback = callback

    def set_delete_callback(self, callback: Optional[Callable]):
        self.__delete_callback = callback

    def add_manual_table(self, name: str, hash_key: KeyDefinition, range_key: Optional[KeyDefinition] = None):
        t = Table(name, hash_key, range_key)
        self.tables[name] = t

    def __get_table(self, name: str) -> Table:
        t = self.tables.get(name)
        if t is None:
            raise AwsResourceNotFoundResponseException("GetItem", "Requested resource not found")
        return t

    def put_item(self, **kwargs):
        table_name = kwargs.pop('TableName')
        item = kwargs.pop('Item')
        expr = kwargs.pop('ConditionExpression', None)
        kwargs.pop('ReturnConsumedCapacity', None)
        kwargs.pop('ReturnItemCollectionMetrics', None)
        assert_empty(kwargs)
        replace = expr is None
        self.__get_table(table_name).add(item, replace)
        return {}

    def update_item(self, **kwargs):
        self.update_count += 1
        table_name = kwargs.pop("TableName")
        key = kwargs.pop("Key")
        expr = kwargs.pop("UpdateExpression")
        condition_expr = kwargs.pop("ConditionExpression", None)
        expr_attributes = kwargs.pop("ExpressionAttributeValues", None)
        kwargs.pop('ReturnConsumedCapacity', None)
        kwargs.pop('ReturnItemCollectionMetrics', None)

        assert_empty(kwargs)
        updates = _collect_updates(expr, expr_attributes)
        t = self.__get_table(table_name)

        if self.__update_callback:
            c = self.__update_callback
            self.__update_callback = None
            c()
        current = t.find_by_example(key)
        if current is None:
            current = {}

        if condition_expr is not None:
            conditions = _parse_conditions(condition_expr)
            conditions.validate("UpdateItem", current, expr_attributes)
        current.update(updates)
        return {}

    def delete_item(self, **kwargs):
        table_name = kwargs.pop('TableName')
        key = kwargs.pop('Key')
        rv = kwargs.pop('ReturnValues', None)
        expr = kwargs.pop('ConditionExpression', None)
        if len(kwargs) != 0:
            raise AssertionError(f"Unrecognized properties: {','.join(kwargs.keys())}")

        parsed = _parse_expression(expr) if expr is not None else None
        if self.__delete_callback is not None:
            dc = self.__delete_callback
            self.__delete_callback = None
            dc()

        if parsed is not None:
            if parsed.action != 'attribute_exists':
                raise NotImplementedError(f"Unsupported expression: {expr}")
            v = self.__get_table(table_name).get(key)
            if v is None or parsed.attribute not in v:
                raise ConditionalCheckFailedException("DeleteItem")

        v = self.__get_table(table_name).remove(key)
        record = {}

        if v is not None and rv == 'ALL_OLD':
            record['Attributes'] = v
        return record

    def get_item(self, **kwargs):
        table_name = kwargs.pop('TableName')
        key = kwargs.pop('Key')
        kwargs.pop("ConsistentRead", None)
        if len(kwargs) != 0:
            raise AssertionError(f"Unrecognized properties: {','.join(kwargs.keys())}")

        v = self.__get_table(table_name).get(key)
        if v is None:
            return {}
        return {"Item": deepcopy(v)}

    def transact_write_items(self, **kwargs):
        items: List[Dict[str, Any]] = kwargs.pop('TransactItems')
        if len(items) == 0:
            return None
        if len(items) > 100:
            raise AssertionError("too many items")
        assert_empty(kwargs)
        save_tables = deepcopy(self.tables)
        ok = False
        try:
            cancel_reasons = []
            error_count = 0
            for item in items:
                keys = item.keys()
                if len(keys) != 1:
                    raise_invalid_parameter("TransactWriteItems", f"Too many values in {item}")
                action = next(iter(keys))
                content = next(iter(item.values()))
                try:
                    if action == 'Put':
                        self.put_item(**content)
                    elif action == 'Delete':
                        self.delete_item(**content)
                    elif action == 'Update':
                        self.update_item(**content)
                    else:
                        raise_invalid_parameter("TransactWriteItems", f"Unsupported action {action} "
                                                                      f"in {item}")
                    cancel_reasons.append({'Code': 'None'})
                except AwsInvalidRequestResponseException as ex:
                    raise ex
                except AwsExceptionResponseException as ex:
                    cancel_reasons.append({'Code': f"{ex.response['Error']['Code']}",
                                           'Message': {ex.response['Error']['Message']}})
                    error_count += 1
            if error_count > 0:
                raise AwsTransactionCanceledException(cancel_reasons)
            ok = True
        finally:
            if not ok:
                self.tables = save_tables

    def scan(self, **kwargs):
        table_name = kwargs.pop('TableName')
        select = kwargs.pop('Select')
        assert select == "ALL_ATTRIBUTES"
        t = self.__get_table(table_name)
        cloned = list(map(lambda row: row.copy(), t.rows.values()))
        return {
            'Items': cloned
        }

    def query(self, **kwargs):
        table_name = kwargs.pop('TableName')
        select = kwargs.pop('Select')
        assert select == "ALL_ATTRIBUTES"

        key_condition_exp = kwargs.pop('KeyConditionExpression')
        exp_attributes: Dict[str, Dict[str, Any]] = kwargs.pop('ExpressionAttributeValues')

        assert_empty(kwargs)

        expr = _parse_condition_expression(key_condition_exp)

        partition_key = {expr.left: exp_attributes.pop(expr.right)}

        t = self.__get_table(table_name)

        cloned = list(map(lambda row: row.copy(), t.query(partition_key)))
        return {
            'Items': cloned
        }
