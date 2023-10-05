from base_test import BaseTest
from request import GoneException
from session_repo import Session


class InstanceTest(BaseTest):

    def test_fail_to_notify(self):
        # Cover code in Instance that logs the failure to notify
        self.sns_mock.set_fail_on_next_publish()
        self.instance.notify_error("Hello!", "Message")
        self.assertEqual(1, self.sns_mock.notify_error_count)

    def test_gone(self):
        session = Session(
            "some-id",
            "token",
            12
        )

        self.assertRaises(GoneException, lambda: self.instance.extend_session(session))
