import urllib.parse
from collections import namedtuple
from typing import Dict, Optional, Any, Union, List
from urllib.parse import urlunparse

_EMPTY_DICT = {}


class Path:
    def __init__(self, path: str):
        parts = split_path(path)
        self.path = path
        self.parts = []
        self.part_names = {}
        self.part_indices = {}
        index = 0
        for p in parts:
            name = p
            if p.startswith("{") and p.endswith("}"):
                var_name = p[1:len(p) - 1:]
                if var_name in self.part_names:
                    raise ValueError(f"Duplicate path variable name {var_name} in {path}")
                name = "?"
                self.part_names[var_name] = index
                self.part_indices[index] = var_name
            self.parts.append(name)
            index += 1

    def has_path_variable(self, name: str) -> bool:
        return name in self.part_names

    def matches(self, path: str) -> Optional[Dict[str, str]]:
        if len(self.part_names) == 0 and self.path == path:
            return _EMPTY_DICT
        parts = split_path(path)
        if len(parts) != len(self.parts):
            return None
        variables = {}
        for i in range(len(parts)):
            our_part = self.parts[i]
            that_part = parts[i]
            if our_part == "?":
                variables[self.part_indices[i]] = decode_from_url(that_part)
            elif our_part != that_part:
                return None
        return variables


def split_path(path: str) -> List[str]:
    return list(filter(lambda part: len(part) > 0, path.split("/")))


def decode_from_url(text: str) -> str:
    return urllib.parse.unquote(text)


def encode_for_url(text: str) -> str:
    return urllib.parse.quote(text, safe='')


def join_paths(*args) -> str:
    path = ""
    for arg in args:
        if len(path) > 0 and not path.endswith("/") and not arg.startswith("/"):
            path += "/"
        path += arg
    return path.replace("//", "/")


def join_base_path(*args) -> str:
    path = join_paths(*args)
    if not path.endswith("/"):
        path += '/'
    return path.replace("//", "/")


def parse_query_string(query: Optional[Union[str, dict]]) -> Optional[Dict[str, Any]]:
    if query is None:
        return None
    if len(query) == 0:
        return _EMPTY_DICT
    if type(query) is dict:
        return query
    results = urllib.parse.parse_qs(query)
    fixed = {}
    for key, value in results.items():
        fixed[key] = ",".join(value)
    return fixed


def get_path(url: str) -> str:
    return urllib.parse.urlparse(url).path


Components = namedtuple(
    typename='Components',
    field_names=['scheme', 'netloc', 'url', 'path', 'query', 'fragment']
)


def replace_host(url: str, new_host: str):
    parsed = urllib.parse.urlparse(url)
    new_url = urlunparse(Components(
        scheme=parsed.scheme,
        netloc=new_host,
        query=parsed.query,
        url=parsed.path,
        path='',
        fragment=parsed.fragment))
    return new_url
