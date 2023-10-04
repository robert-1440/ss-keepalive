from typing import Any, Dict


class Subscription:
    def __init__(self, node: Dict[str, Any]):
        self.arn = node['SubscriptionArn']
        self.owner = node.get('Owner')
        self.protocol = node.get('Protocol')
        self.endpoint = node.get('Endpoint')
        self.topic_arn = node.get("TopicArn")


class Sns:
    def __init__(self, client: Any):
        self.__client = client

    def publish(self, topic_arn: str, subject: str, message: str):
        self.__client.publish(TopicArn=topic_arn,
                              Subject=subject,
                              Message=message)
