import os
from typing import Dict, Any

import app
from bean import BeanName, beans
from bean.beans import get_bean_instance
from better_test_case import BetterTestCase
from instance import Instance

# Protect us from accidentally hitting an actual AWS account
os.environ['AWS_ACCESS_KEY_ID'] = "invalid"
os.environ['AWS_SECRET_ACCESS_KEY'] = "invalid"
os.environ['SS_KEEPALIVE_ERROR_TOPIC_ARN'] = 'fake-arn'


class BaseTest(BetterTestCase):
    instance: Instance

    def setUp(self) -> None:
        self.instance = get_bean_instance(BeanName.INSTANCE)

    @staticmethod
    def invoke_event(event: Dict[str, Any]):
        return app.handler(event, None)

    def tearDown(self) -> None:
        beans.reset()
