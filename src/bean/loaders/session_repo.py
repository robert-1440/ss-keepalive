from typing import Any

from bean import BeanName
from bean.beans import inject
from session_repo.aws_session_repo import AwsSessionRepo


@inject(bean_instances=BeanName.DYNAMODB_CLIENT)
def init(client: Any):
    return AwsSessionRepo(client)