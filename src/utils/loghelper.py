import logging
import os.path
import sys
from logging import Logger, Formatter, StreamHandler
from types import ModuleType
from typing import Union

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d [%(process)6d] %(levelname)-7s:  %(name)-20s  %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S')

formatter = Formatter('%(asctime)s.%(msecs)03d [%(process)6d] %(levelname)-7s:  %(name)-20s  %(message)s',
                      datefmt='%m/%d/%Y %H:%M:%S')

handler = StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)


def __extract_name(name: Union[ModuleType, str]) -> str:
    if isinstance(name, ModuleType):
        fn = name.__file__
        if not os.path.isabs(fn):
            fn = os.path.realpath(fn)
        name = name.__name__
        index = fn.find("/src/")
        if index > 0:
            s = fn[index + 5::]
            index = s.rfind(".py")
            if index > 0:
                name = s[0:index:].replace("/", ".")
    return name


def get_logger(name: Union[ModuleType, str]) -> Logger:
    name = __extract_name(name)
    logger = logging.Logger(name, level=logging.INFO)
    logger.addHandler(handler)
    return logger


def get_module_logger(name: str):
    return get_logger(sys.modules[name])
