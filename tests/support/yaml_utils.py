from typing import List, Union

import yaml
from yaml import SafeLoader
from yaml.composer import Composer
from yaml.constructor import Constructor


def parse_yaml_file(file_name: str, include_line_numbers=True) -> dict:
    """
    Parses the given file.

    :param file_name: the file name.
    :param include_line_numbers: True to include line numbers in the resulting dict, the key is __line__.
    :return: the parsed dict
    """
    with open(file_name, "r") as f:
        return parse_yaml(f, include_line_numbers=include_line_numbers)


def parse_yaml_documents(file_name: str) -> List[dict]:
    with open(file_name, "r") as f:
        return list(yaml.load_all(f, Loader=SafeLoader))


def parse_yaml(stream: Union[str, bytes], include_line_numbers=True, as_list: bool = False) -> Union[dict, List[dict]]:
    """
    Parses the given stream as .yaml.

    :param stream: the stream.
    :param include_line_numbers: True to include line numbers in the resulting dict, the key is __line__.
    :param as_list: True to always return the nodes as a list. Used in cases where you nodes multiple documents.
    :return: the parsed dict
    """
    loader = yaml.Loader(stream)

    def compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        node.__line__ = line + 1
        return node

    def construct_mapping(node, deep=False):
        mapping = Constructor.construct_mapping(loader, node, deep=deep)
        if include_line_numbers:
            mapping['__line__'] = node.__line__
        return mapping

    loader.compose_node = compose_node
    loader.construct_mapping = construct_mapping
    results = []
    while True:
        data = loader.get_data()
        if data is None:
            break
        results.append(data)

    if not as_list and len(results) == 1:
        return results[0]

    return results


def to_yaml(record: dict, indent: int = None, sort_keys: bool = False,
            default_flow_style: bool = False) -> str:
    text = yaml.dump(record, sort_keys=sort_keys, default_flow_style=default_flow_style)
    if indent is not None and indent > 0:
        text = __reindent(text, indent)
    return text

def __reindent(string: str, num_spaces: int):
    s = string.splitlines(keepends=False)
    spaces = num_spaces * ' '
    s = [spaces + line for line in s]
    return '\n'.join(s)

