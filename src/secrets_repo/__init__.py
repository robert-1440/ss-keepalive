import abc
import json
from typing import Optional, Union, Any, Dict


class GcpCredentials:
    def __init__(self, content: Dict[str, Any]):
        self.content = content

    @classmethod
    def from_json(cls, data: Optional[Union[str, dict]]):
        if data is None:
            return None
        record = data if isinstance(data, dict) else json.loads(data)
        return GcpCredentials(record)


class SecretsRepo(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def find_gcp_credentials(self) -> Optional[GcpCredentials]:
        raise NotImplementedError()
