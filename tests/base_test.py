import os
from typing import Dict, Any, Optional, Union

import app
from bean import BeanName, beans
from bean.beans import get_bean_instance
from better_test_case import BetterTestCase
from botomocks.dynamodb_mock import MockDynamoDbClient, KeyPart, KeyDefinition
from botomocks.scheduler_mock import MockSchedulerClient
from botomocks.sm_mock import MockSecretsManagerClient
from botomocks.sns_mock import MockSnsClient, Notification
from instance import Instance
import json

from mocks.gcp import firebase_admin
from mocks.gcp.firebase_admin import messaging

from mocks.gcp.firebase_admin.messaging import Invocation

SCHEDULE_ROLE_ARN = 'ScheduleRoleArn'

NOTIFICATION_GROUP = 'NotificationGroup'

KEEPALIVE_ERROR_ARN = 'keepalive-error-arn'

# Protect us from accidentally hitting an actual AWS account
os.environ['AWS_ACCESS_KEY_ID'] = "invalid"
os.environ['AWS_SECRET_ACCESS_KEY'] = "invalid"

os.environ['SS_KEEPALIVE_ERROR_TOPIC_ARN'] = KEEPALIVE_ERROR_ARN
os.environ['SS_KEEPALIVE_SCHEDULE_GROUP'] = NOTIFICATION_GROUP
os.environ['SS_KEEPALIVE_SCHEDULE_GROUP_ROLE_ARN'] = SCHEDULE_ROLE_ARN

ROOT = "/ss/"

FUNCTION_ARN = "arn:aws:lambda:us-west-1:123456789012:function:ssKeepaliveService"


class Context:
    def __init__(self):
        self.invoked_function_arn = FUNCTION_ARN


_CONTEXT = Context()


class InvokeResponse:
    status_code: int
    body: Dict[str, Any]
    raw_body: str
    error_message: Optional[str]

    def __init__(self, resp: Dict[str, Any]):
        self.status_code = resp['statusCode']
        self.raw_body = body = resp.get('body')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except Exception:
                body = None
        self.body = body
        if self.status_code // 100 != 2:
            self.error_message = self.body['errorMessage']
        else:
            self.error_message = None

    def assert_result(self, status_code: int = None, error_message: str = None):
        if status_code is not None:
            assert status_code == self.status_code, f"Expected status code of {status_code}, got {self.status_code}"
        else:
            if self.status_code // 100 != 2:
                raise AssertionError(f"Call failed: {self.status_code} - {self.body}")
        if error_message is not None:
            assert error_message == self.error_message, (f"Expected error message '{error_message}, "
                                                         f"got {self.error_message}")


def _setup_ddb(client: MockDynamoDbClient) -> MockDynamoDbClient:
    part = KeyPart('sessionId', "S")
    hash_key = KeyDefinition([part])
    client.add_manual_table("SSKeepaliveSession", hash_key)
    return client


def install_gcp_cert(client: MockSecretsManagerClient):
    record = {
        'private_key_id': "some-key",
        "private_key": 'some-private-key'
    }
    client.create_secret(Name="ss-keepalive/GcpCertificate",
                         Description="GCP creds",
                         SecretString=json.dumps(record))

    def cert_builder(content: str):
        return {'content': content}

    beans.override_bean(BeanName.GCP_CERT_BUILDER, lambda: cert_builder)


class BaseTest(BetterTestCase):
    instance: Instance

    def setUp(self) -> None:
        self.sm_mock = MockSecretsManagerClient()
        self.ddb_mock = _setup_ddb(MockDynamoDbClient())
        self.sns_mock = MockSnsClient()
        self.scheduler_mock = MockSchedulerClient()

        install_gcp_cert(self.sm_mock)
        beans.override_bean(BeanName.FIREBASE_ADMIN, firebase_admin)

        beans.override_bean(BeanName.SECRETS_MANAGER_CLIENT, self.sm_mock)
        beans.override_bean(BeanName.DYNAMODB_CLIENT, self.ddb_mock)
        beans.override_bean(BeanName.SNS_CLIENT, self.sns_mock)
        beans.override_bean(BeanName.SCHEDULER_CLIENT, self.scheduler_mock)

        self.instance = get_bean_instance(BeanName.INSTANCE)

    @staticmethod
    def invoke_event(event: Dict[str, Any]):
        return app.handler(event, None)

    def __construct_event(self,
                          path: str,
                          method: str,
                          in_headers: Dict[str, Any] = None,
                          body: Union[str, Dict[str, Any]] = None,
                          ) -> Dict[str, Any]:
        if type(body) is dict:
            body = json.dumps(body)
        headers = dict(in_headers) if in_headers else {}
        event = {
            "rawPath": path,
            "headers": headers,
            "requestContext": {
                "http": {
                    "method": method,
                    "sourceIp": "127.0.0.1"
                }
            },
            "body": body
        }

        return event

    def invoke_web_event(self,
                         path: str,
                         method: str,
                         in_headers: Dict[str, Any] = None,
                         body: Union[str, Dict[str, Any]] = None,
                         expected_status_code: int = None,
                         expected_error_message: str = None) -> InvokeResponse:
        if path.startswith("/"):
            path = path[1::]
        path = f"{ROOT}{path}"
        event = self.__construct_event(path, method, in_headers, body)
        resp_json = app.handler(event, _CONTEXT)
        if resp_json is None:
            resp_dict = {'statusCode': 200}
        else:
            resp_dict = json.loads(resp_json)
        resp = InvokeResponse(resp_dict)
        resp.assert_result(expected_status_code, expected_error_message)
        return resp

    def tearDown(self) -> None:
        beans.reset()
        messaging.reset()

    @staticmethod
    def pop_push_notification() -> Invocation:
        return messaging.pop_invocation()

    @staticmethod
    def assert_no_push_notifications():
        messaging.assert_no_invocations()

    def assert_no_notifications(self):
        return self.sns_mock.assert_no_notifications()

    def pop_notification(self) -> Notification:
        return self.sns_mock.pop_notification()

    @staticmethod
    def add_invalid_push_token(token: str):
        messaging.add_invalid_token(token)
