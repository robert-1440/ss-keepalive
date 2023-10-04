from typing import Any

from notifier.aws.sns import Sns
from notifier.notifier import Notifier


class AwsNotifier(Notifier):
    def __init__(self, client: Any, topic_arn: str):
        self.topic_arn = topic_arn
        self.sns = Sns(client)

    def notify_error(self, subject: str, message: str):
        self.sns.publish(self.topic_arn, subject, message)
