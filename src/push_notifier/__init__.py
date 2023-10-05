import abc
from typing import Dict


class PushNotifier(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def notify(self, token: str, data: Dict[str, str], dry_run: bool = False):
        raise NotImplementedError()
