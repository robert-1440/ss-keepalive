import os
from typing import Any

from bean import BeanName
from bean.beans import inject
from notifier.aws_notifier import AwsNotifier


@inject(bean_instances=BeanName.SNS_CLIENT)
def init(client: Any):
    arn = os.environ.get('SS_KEEPALIVE_ERROR_TOPIC_ARN', 'invalid')
    return AwsNotifier(client, arn)
