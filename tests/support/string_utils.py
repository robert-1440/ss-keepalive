from io import StringIO
from typing import Any


class StringBuilder:
    def __init__(self, initial_value: str = None):
        self.__builder = StringIO()
        self.__value = None
        if initial_value is not None:
            self.__builder.write(initial_value)

    def append(self, s: Any):
        if s is None:
            return
        if type(s) is not str:
            s = str(s)
        self.__value = None
        self.__builder.write(s)
        return self

    def append_line(self, content: Any):
        self.append(content)
        self.append_lf()
        return self

    def append_lf(self):
        self.append('\n')
        return self

    def __len__(self):
        return self.__builder.tell()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        if self.__value is None:
            self.__value = self.__builder.getvalue()
        return self.__value

    def is_empty(self):
        return len(self) == 0

    def is_not_empty(self):
        return len(self) > 0

    def remove_chars_from_end(self, size: int):
        total = len(self) - size
        self.__builder.truncate(total)
        self.__builder.seek(total)
        self.__value = None
        return self

    def reset(self):
        if len(self) > 0:
            self.__builder.seek(0)
            self.__builder.truncate(0)
            self.__value = None
        return self

