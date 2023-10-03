from typing import Tuple

from utils.path_utils import join_base_path
from web.lf.router import Method


class Resource:
    def __init__(self, root_url: str, resource_name: str):
        self.__prefix_url = join_base_path(root_url, resource_name)

    def route(self, path: str,
              response_codes: Tuple[int] = (200, 400, 404),
              method: Method = Method.GET):
        def decorator(wrapped_function):
            add_route(join_paths(self.__prefix_url, path), method, wrapped_function, action, response_codes,
                      matcher_required, auth, verify_org_id)

        return decorator
