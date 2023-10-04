import abc
from typing import Dict, Any

from instance import Instance


class InternalEventProcessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def process(self, instance: Instance, event: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()
