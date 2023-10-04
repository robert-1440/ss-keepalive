from typing import Dict, Any

import abc

from instance import Instance
from request import HttpRequest


ROOT_URL = "/ss/keepalive/"


class WebRequestProcessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def process(self, instance: Instance, request: HttpRequest) -> Dict[str, Any]:
        raise NotImplementedError()
