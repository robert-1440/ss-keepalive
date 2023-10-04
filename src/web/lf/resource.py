from typing import Tuple, Collection

from utils.path_utils import join_base_path, join_paths
from web.lf.router import Method, add_route


class Resource:
    def __init__(self, root_url: str, resource_name: str):
        self.__prefix_url = join_base_path(root_url, resource_name)

    def route(self, path: str,
              response_codes: Collection[int] = (200, 400, 404),
              method: Method = Method.GET):
        def decorator(wrapped_function):
            add_route(join_paths(self.__prefix_url, path), method, wrapped_function, response_codes)

        return decorator
