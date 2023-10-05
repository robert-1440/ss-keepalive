import os.path
from io import StringIO
from typing import Dict, Any, Optional, List, Iterable
from support import yaml_utils
from better_test_case import BetterTestCase
from support.string_utils import StringBuilder
from web.lf import router
from web.lf.router import _Route

"""
The purpose of this test is to ensure that the res_api.yaml file contains all the necessary endpoints and
appropriate response codes.
"""

_PATH_PREFIX = "ss/"
_FULL_PATH_PREFIX = f"/{_PATH_PREFIX}"

FUNCTION_NAME = "ssKeepaliveService"
_DEFAULT_RESPONSE_CODES = [401, 404, 415, 500]


def _set_default_response_codes(response_codes: Iterable[int]) -> List[int]:
    response_codes = set(response_codes)
    response_codes.update(_DEFAULT_RESPONSE_CODES)
    r = list(response_codes)
    r.sort()
    return r


class RestApiMethod:
    def __init__(self, route: _Route):
        self.method = route.method.name
        self.response_codes = _set_default_response_codes(route.response_codes)
        path = route.path[len(_FULL_PATH_PREFIX)::]
        self.name = route.method.name.lower() + "-" + extract_method_name(path)

    def build(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'http-method': self.method,
            'lambda-function': FUNCTION_NAME,
            'response-codes': self.response_codes
        }


class YamlMethod:
    def __init__(self, node: Dict[str, Any]):
        self.name = node['name']
        self.http_method = node['http-method']
        self.lamda_function = node['lambda-function']
        self.response_codes = list(map(int, node.get('response-codes', [])))
        self.response_codes.sort()

    def matches(self, method: RestApiMethod):
        return self.lamda_function == FUNCTION_NAME and self.response_codes == method.response_codes


class YamlResource:
    def __init__(self, node: Dict[str, Any]):
        self.path = node['path']
        self.methods = list(map(YamlMethod, node['methods']))

    def find_method(self, api_method: RestApiMethod) -> Optional[YamlMethod]:
        for m in self.methods:
            if m.http_method == api_method.method:
                return m
        return None


def extract_method_name(path: str):
    parts = path.split("/")

    def map_it(p: str):
        if '{' in p:
            return None
        return p

    parts = filter(lambda p: p is not None, map(map_it, parts))
    return "-".join(parts)


def fix_response_codes(text: str):
    start = 0
    while True:
        index = text.find("response-codes:", start)
        if index < 0:
            break
        codes = []
        end_index = text.find(':\n', index)
        block_index = end_index + 2
        while True:
            eol_index = text.find('\n', block_index)
            if eol_index < 0:
                break
            eol_index += 1
            v = text[block_index:eol_index:].strip()
            if v.startswith("- "):
                code = v[2::]
                if code.isdigit():
                    codes.append(v[2::])
                else:
                    break
            else:
                break
            block_index = eol_index

        if len(codes) > 0:
            left = text[0:end_index:] + ": [ " + ", ".join(codes) + " ]\n"
            start = len(left)

            text = left + text[block_index::]
        else:
            start = end_index + 2

    return text


class RestApiResource:
    def __init__(self, path: str):
        self.path = path[1::]
        self.methods: List[RestApiMethod] = []

    def add(self, route: _Route):
        self.methods.append(RestApiMethod(route))

    def check(self, resources: List[YamlResource], sb: StringBuilder):
        def find_resource():
            for r in resources:
                if r.path == self.path:
                    return r
            return None

        r = find_resource()
        if r is None:
            message = f"Missing resource"
        else:
            message = None
            for m in self.methods:
                ym = r.find_method(m)
                if ym is None:
                    if message is None:
                        message = ""
                    message += f"Missing method {m.method}\n"
                elif not ym.matches(m):
                    if message is None:
                        message = ""

                    message += f"Method {m.method} does not match.\n"
                    message += f"{m.response_codes} vs {ym.response_codes}\n"

        if message is not None:
            sb.append(message).append(' For ').append_line(self.path)
            io = StringIO()
            y = fix_response_codes(yaml_utils.to_yaml(self.build(), indent=2) + '\n')

            print(f"Suggested changes:\n{y}",
                  file=io)
            sb.append(io.getvalue())

    def build(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'methods': list(map(lambda m: m.build(), self.methods))
        }


class TestCase(BetterTestCase):

    def test_verify(self):
        parent = os.path.split(__file__)[0]
        file_name = os.path.join(parent, "../infra/src/rest-api.yaml")
        node = yaml_utils.parse_yaml_file(file_name, include_line_numbers=False)
        resources = list(map(lambda n: YamlResource(n), node['resources']))
        resource_set = set()
        for r in resources:
            path = r.path
            if path in resource_set:
                raise AssertionError(f"path {r.path} is duplicated.")
            resource_set.add(path)

        routes = getattr(router, "_routes")
        assert len(routes) > 0

        api_resources = {}
        for r in routes.values():
            path = r.path[len(_PATH_PREFIX)::]
            api_route = api_resources.get(path)
            if api_route is None:
                api_route = RestApiResource(path)
                api_resources[path] = api_route
            api_route.add(r)

        sb = StringBuilder()
        for ar in api_resources.values():
            ar.check(resources, sb)

        if sb.is_not_empty():
            raise AssertionError(sb.to_string())
