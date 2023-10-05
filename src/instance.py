from typing import Optional

from notifier.notifier import Notifier
from push_notifier import PushNotifier
from request import NotFoundException, GoneException
from scheduler import Scheduler
from secrets_repo import SecretsRepo
from session_repo import SessionRepo, Session
from utils import exception_utils, loghelper

logger = loghelper.get_logger(__name__)

# 4 hours
_TTL_SECONDS = 14400


class Instance:
    def __init__(self,
                 secrets_repo: SecretsRepo,
                 session_repo: SessionRepo,
                 scheduler: Scheduler,
                 push_notifier: PushNotifier,
                 notifier: Notifier):
        self.__secrets_repo = secrets_repo
        self.__session_repo = session_repo
        self.__scheduler = scheduler
        self.__push_notifier = push_notifier
        self.__notifier = notifier
        self.__function_arn: Optional[str] = None

    def set_function_arn(self, arn: str):
        self.__function_arn = arn

    def has_function_arn(self):
        return self.__function_arn is not None

    def test_push_notification(self, token: str) -> Optional[str]:
        """
        Attempt a push notification as a dry-run.

        :param token: the FCM device token.
        :return: None if the test passed, otherwise a string with the error message.
        """
        record = {'type': 'keepalive-test'}
        try:
            self.__push_notifier.notify(token, record, dry_run=True)
        except Exception as ex:
            return exception_utils.get_exception_message(ex)
        return None

    def send_push_notification(self, token: str, session_id: str):
        record = {
            'type': 'keepalive',
            'sessionId': session_id
        }
        try:
            self.__push_notifier.notify(token, record)
        except Exception:
            self.notify_error("Failed to send push notification", exception_utils.dump_ex())

    def notify_error(self, subject: str, message: str) -> bool:
        logger.error(f"{subject}:\n{message}")
        try:
            self.__notifier.notify_error(subject, message)
            return True
        except Exception:
            logger.error(f"Failed to notify error: {exception_utils.dump_ex()}")

    def create_session(self, session: Session) -> bool:
        return self.__session_repo.create_session(session, _TTL_SECONDS)

    def extend_session(self, session: Session):
        if not self.__session_repo.extend_session(session, _TTL_SECONDS):
            # We raise gone because it must have existed in order to call this
            raise GoneException(f"Session with id {session.session_id} no longer exists.")

    def find_session(self, session_id: str) -> Optional[Session]:
        return self.__session_repo.find_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self.__session_repo.delete_session(session_id)

    def create_schedule(self, session_id: str, future_seconds: int) -> bool:
        assert self.__function_arn is not None
        return self.__scheduler.create_schedule(self.__function_arn, session_id, future_seconds)

    def delete_schedule(self, session_id: str) -> bool:
        return self.__scheduler.delete_schedule(session_id)
