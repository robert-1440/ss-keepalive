from typing import Any

from bean import BeanName
from bean.beans import inject
from secrets_repo.aws_secrets_repo import AwsSecretsRepo
from session_repo.aws_session_repo import AwsSessionRepo


@inject(bean_instances=BeanName.SECRETS_MANAGER_CLIENT)
def init(client: Any):
    return AwsSecretsRepo(client)
