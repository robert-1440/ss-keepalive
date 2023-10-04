from typing import Any, Optional

from aws import is_not_found_exception, is_invalid_request
from secrets_repo import SecretsRepo, GcpCredentials


class AwsSecretsRepo(SecretsRepo):

    def __init__(self, client: Any):
        self.client = client

    def find_gcp_credentials(self) -> Optional[GcpCredentials]:
        return GcpCredentials.from_json(self.__get_secret_value("ss-keepalive/GcpCertificate"))

    def __get_secret_value(self, name: str) -> Optional[str]:
        try:
            response = self.client.get_secret_value(SecretId=name)
        except Exception as ex:
            if is_not_found_exception(ex) or is_invalid_request(ex):
                return None
            raise ex
        return response['SecretString']
