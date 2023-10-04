import os
from typing import Any

from bean import BeanName
from bean.beans import inject
from scheduler.aws_scheduler import AwsScheduler


@inject(bean_instances=BeanName.SCHEDULER_CLIENT)
def init(client: Any):
    group_name = os.environ.get('SS_KEEPALIVE_SCHEDULE_GROUP', 'default')
    role_arn = os.environ.get('SS_KEEPALIVE_SCHEDULE_GROUP_ROLE_ARN', 'bad')
    return AwsScheduler(client, group_name, role_arn)
