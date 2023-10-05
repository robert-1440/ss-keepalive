import json
import time
from datetime import datetime
from typing import Optional

import bean.beans
from aws.dynamodb import DynamoDb
from base_test import BaseTest, NOTIFICATION_GROUP, FUNCTION_ARN, SCHEDULE_ROLE_ARN
from bean import BeanName
from botomocks.scheduler_mock import Schedule
from mocks.gcp.firebase_admin import messaging
from session_repo import Session
from utils import date_utils
from utils.date_utils import get_system_time_in_seconds

_DEFAULT_TOKEN = "ThisIsAnFcmToken"
_DEFAULT_SESSION_ID = "this-is-a-session-id"


class SessionsTest(BaseTest):

    def test_create(self):
        exp_time = date_utils.calc_expire_time_in_epoch_seconds(14400)

        self.create_session()

        # Ensure it really made it
        sess = self.get_session()
        self.assertEqual(_DEFAULT_SESSION_ID, sess.session_id)
        self.assertEqual(_DEFAULT_TOKEN, sess.fcm_device_token)
        self.assertEqual(60, sess.interval_seconds)
        self.assertEqual(0, sess.state_counter)

        self.assertIsNotNone(sess.expire_time)
        diff = sess.expire_time - exp_time
        if diff > 1 or diff < 0:
            self.fail(f"Bad expire time: {sess.expire_time}")

        # Make sure it created a schedule
        schedule = self.get_schedule()
        self._validate_schedule(schedule)

        # Already exists
        self.create_session(
            expected_status_code=409,
            expected_error_message="Session with id this-is-a-session-id already exists."
        )

        # Hack it such that creating the schedule fails because it exists
        self.scheduler_mock.set_raise_exists_on_next_create()
        self.create_session(
            session_id="new-one",
            expected_status_code=409,
            expected_error_message="Schedule already exists."
        )
        # Make sure the session is not lingering
        self.assertIsNone(self.instance.find_session('new-one'))

    def test_create_with_bad_args(self):
        self.create_session(
            interval_minutes=0,
            expected_status_code=400,
            expected_error_message="Invalid intervalMinutes: 0, must be between 1 and 1440."
        )

        self.create_session(
            interval_minutes=1441,
            expected_status_code=400,
            expected_error_message="Invalid intervalMinutes: 1441, must be between 1 and 1440."
        )

        # Invalid session id
        self.create_session(
            session_id="that's bad",
            expected_status_code=400,
            expected_error_message="Invalid session id: 'that's bad', must be alpha-numeric."
        )

        # Extra args
        self.create_session(
            expected_status_code=400,
            expected_error_message="The following properties are not recognized: someParam.",
            someParam=False
        )

        # Bad token
        self.add_invalid_push_token("bad-token")
        self.create_session(
            token='bad-token',
            expected_status_code=400,
            expected_error_message="Invalid fcmToken: Invalid token: bad-token."
        )

        # Missing params
        self.create_session(
            session_id=None,
            expected_status_code=400,
            expected_error_message="Missing parameter 'sessionId'."
        )

        self.create_session(
            token=None,
            expected_status_code=400,
            expected_error_message="Missing parameter 'fcmToken'."
        )

        self.create_session(
            interval_minutes=None,
            expected_status_code=400,
            expected_error_message="Missing parameter 'intervalMinutes'."
        )

    def test_delete(self):
        self.delete_session(session_id="some-session",
                            expected_status_code=404,
                            expected_error_message="Resource Not Found: Session with id some-session does not exist.")
        self.create_session()

        # Sanity
        self.assertIsNotNone(self.instance.find_session(_DEFAULT_SESSION_ID))
        self.get_schedule()

        self.delete_session()
        self.assertIsNone(self.instance.find_session(_DEFAULT_SESSION_ID))
        self.assertIsNone(self.find_schedule())

    def test_keep_alive(self):
        self.send_keepalive(
            expected_status_code=404,
            expected_error_message=f"Resource Not Found: Session with id {_DEFAULT_SESSION_ID} does not exist."
        )

        self.create_session()

        sess = self.get_session()

        time.sleep(1)
        self.send_keepalive()

        after_sess = self.get_session()
        self.assertNotEquals(sess, after_sess)
        self.assertEqual(sess.state_counter + 1, after_sess.state_counter)
        self.assertGreater(after_sess.expire_time, sess.expire_time)

    def test_lambda_invocation(self):
        self.create_session()
        n = messaging.pop_invocation()
        self.assertTrue(n.dry_run)
        s = self.get_schedule()

        self.invoke_lambda(s)

        n = messaging.pop_invocation()
        self.assertEqual(n.token, _DEFAULT_TOKEN)
        self.assertEqual({'sessionId': 'this-is-a-session-id', 'type': 'keepalive'}, n.data)
        self.assert_no_push_notifications()

        self.assert_no_notifications()

        # Test failure
        self.add_invalid_push_token(_DEFAULT_TOKEN)
        self.invoke_lambda(s)
        self.assert_no_push_notifications()

        nn = self.pop_notification()
        self.assertIn("ValueError: Invalid token: ThisIsAnFcmToken", nn.message)
        self.assertEqual('Failed to send push notification', nn.subject)

        # Now, test with it being expired
        stamp = get_system_time_in_seconds() - 14410
        ddb: DynamoDb = bean.beans.get_bean_instance(BeanName.DYNAMODB)
        ddb.update_item("SSKeepaliveSession",
                        keys={"sessionId": _DEFAULT_SESSION_ID},
                        item={
                            'expireTime': stamp
                        })

        self.invoke_lambda(s)
        self.assertIsNone(self.find_schedule(_DEFAULT_SESSION_ID))

    ##############################################################################################
    # Support methods
    ##############################################################################################
    def create_session(self, session_id: Optional[str] = _DEFAULT_SESSION_ID,
                       token: Optional[str] = _DEFAULT_TOKEN,
                       interval_minutes: Optional[int] = 1,
                       expected_status_code: int = 204,
                       expected_error_message: str = None,
                       **kwargs):
        body = {}
        if session_id is not None:
            body['sessionId'] = session_id
        if token is not None:
            body['fcmToken'] = token
        if interval_minutes is not None:
            body['intervalMinutes'] = interval_minutes

        if len(kwargs) > 0:
            body.update(kwargs)
        self.invoke_web_event(path="sessions",
                              method="POST",
                              body=body,
                              expected_status_code=expected_status_code,
                              expected_error_message=expected_error_message)

    def send_keepalive(self,
                       session_id: str = _DEFAULT_SESSION_ID,
                       body: str = None,
                       expected_status_code: int = 204,
                       expected_error_message: str = None
                       ):

        self.invoke_web_event(path=f"sessions/{session_id}/actions/keepalive",
                              method="POST",
                              body=body,
                              expected_status_code=expected_status_code,
                              expected_error_message=expected_error_message)

    def delete_session(self,
                       session_id: str = _DEFAULT_SESSION_ID,
                       expected_status_code: int = 204,
                       expected_error_message: str = None
                       ):
        self.invoke_web_event(path=f"sessions/{session_id}",
                              method="DELETE",
                              expected_status_code=expected_status_code,
                              expected_error_message=expected_error_message)

    def find_schedule(self, session_id: str = _DEFAULT_SESSION_ID) -> Optional[Schedule]:
        return self.scheduler_mock.find_schedule_by_session(NOTIFICATION_GROUP, session_id)

    def get_schedule(self, session_id: str = _DEFAULT_SESSION_ID) -> Schedule:
        s = self.find_schedule(session_id)
        if s is None:
            self.fail(f"Unable to find schedule for session {session_id}")
        return s

    def _validate_schedule(self, schedule: Schedule, session_id=_DEFAULT_SESSION_ID):
        self.assertEqual(NOTIFICATION_GROUP, schedule.group_name)
        self.assertEqual("rate(1 minutes)", schedule.schedule_expression)
        start_dt = schedule.start_date
        self.assertIsNotNone(start_dt)
        self.assertGreater(start_dt, datetime.utcnow())
        self.assertEqual({'Mode': 'OFF'}, schedule.flexible_time_window)

        target = schedule.target
        self.assertEqual(FUNCTION_ARN, target.arn)
        self.assertEqual(target.role_arn, SCHEDULE_ROLE_ARN)
        record = json.loads(target.input)
        self.assertEqual({'internalEvent': {'type': 'keepalive', 'sessionId': session_id}}, record)

    def find_session(self, session_id: str = _DEFAULT_SESSION_ID) -> Optional[Session]:
        return self.instance.find_session(session_id)

    def get_session(self, session_id: str = _DEFAULT_SESSION_ID) -> Session:
        sess = self.find_session(session_id)
        if sess is None:
            self.fail(f"Session {session_id} not found")
        return sess

    def invoke_lambda(self, schedule: Schedule):
        self.invoke_event(json.loads(schedule.target.input))
