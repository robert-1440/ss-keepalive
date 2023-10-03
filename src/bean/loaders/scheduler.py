

from typing import Any

from bean import BeanName
from bean.beans import inject
from scheduler.aws_scheduler import AwsScheduler


@inject(bean_instances=BeanName.SCHEDULER_CLIENT)
def init(client: Any):
    return AwsScheduler(client)
