from enum import Enum
from typing import Callable, Dict, Optional, Tuple, Any

from instance import Instance
from request import HttpRequest, Response, NotFoundException, \
    MethodNotAllowedException
from utils.path_utils import Path


class Method(Enum):
    GET = 0,
    POST = 1,
    PATCH = 2
    PUT = 3,
    DELETE = 4

    def body_allowed(self):
        return self == Method.POST or self == Method.PATCH or self == Method.PUT


class _Route:
    def __init__(self, path: str, method: Method, caller: Callable,
                 response_codes: Tuple[int]):
        self.has_query_params = path.endswith("?")
        if self.has_query_params:
            path = path[0:len(path) - 1:]
        self.path = path
        self.match_path = Path(path)
        self.method = method
        self.caller = caller
        self.response_codes = response_codes

    def path_matches(self, path: str) -> Dict[str, str]:
        return self.match_path.matches(path)

    def invoke(self, instance: Instance,
               request: HttpRequest,
               params: Dict[str, Any]) -> Response:
        include_request = False
        args = [instance]

        if include_request or self.method.body_allowed():
            args.append(request)

        return self.caller(*args, **params)


_routes: Dict[str, _Route] = {}


def __find_route(path: str) -> Optional[_Route]:
    for r in filter(lambda r: r.path_matches(path) is not None, _routes.values()):
        return r
    return None


def __find_full_route(path: str, method: str) -> Optional[Tuple[_Route, Dict[str, str]]]:
    for r in filter(lambda r: r.method.name == method, _routes.values()):
        r: _Route
        v = r.path_matches(path)
        if v is not None:
            return r, v
    return None


def add_route(path: str, method: Method, caller: Callable,
              response_codes: Tuple[int]):
    key = f"{method.name}:{path}"
    if key in _routes:
        raise AssertionError(f"{key} route has already been added.")
    _routes[key] = _Route(path, method, caller, response_codes)


def process(instance: Instance, request: HttpRequest):
    path = request.path
    result = __find_full_route(path, request.method)
    if result is None:
        f = __find_route(path)
        if f is None:
            print(f"Unable to find {path}")
            raise NotFoundException()
        else:
            raise MethodNotAllowedException()
    f = result[0]
    params = result[1]
    return f.invoke(instance, request, params)
