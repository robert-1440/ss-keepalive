import abc
from typing import Dict


class PushNotifier(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def notify(self, token: str, data: Dict[str, str]):
        raise NotImplementedError()
