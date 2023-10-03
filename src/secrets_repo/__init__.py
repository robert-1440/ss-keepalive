import json
from typing import Optional, Union

import abc


class GcpCredentials:
    def __init__(self, project_id: str,
                 private_key: str):
        self.project_id = project_id
        self.private_key = private_key

    @classmethod
    def from_json(cls, data: Optional[Union[str, dict]]):
        if data is None:
            return None
        record = data if isinstance(data, dict) else json.loads(data)
        return GcpCredentials(record['projectId'], record['privateKey'])


class SecretsRepo(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def find_gcp_credentials(self) -> Optional[GcpCredentials]:
        raise NotImplementedError()
