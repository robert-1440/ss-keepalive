import abc
from enum import Enum
from typing import Any


class BeanName(Enum):
    SCHEDULER = 0
    DYNAMODB_CLIENT = 1
    DYNAMODB = 2
    SECRETS_MANAGER_CLIENT = 3
    INSTANCE = 4
    SCHEDULER_CLIENT = 5
    SECRETS_REPO = 6
    SESSION_REPO = 7
    WEB_ROUTER = 8
    INTERNAL_ROUTER = 9
    GCP_CREDS = 10
    FIREBASE_ADMIN = 11
    PUSH_NOTIFIER = 12
    NOTIFIER = 13
    SNS_CLIENT = 14


class Bean(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_instance(self) -> Any:
        raise NotImplementedError()
