from typing import Any

from bean import BeanName
from bean.beans import inject
from instance import Instance


@inject(bean_instances=BeanName.INSTANCE)
def __get_instance(instance: Instance):
    return instance


def handler(event: dict, context: Any):
    pass
