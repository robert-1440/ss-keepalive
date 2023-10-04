from notifier.notifier import Notifier
from push_notifier import PushNotifier
from scheduler import Scheduler
from secrets_repo import SecretsRepo
from session_repo import SessionRepo, Session
from utils import exception_utils, loghelper

logger = loghelper.get_logger(__name__)


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

    def push_notification(self, token: str, session_id: str):
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
        return self.__session_repo.create_session(session)

    def create_schedule(self, function_url: str, session_id: str, future_seconds: int) -> bool:
        return self.__scheduler.create_schedule(function_url, session_id, future_seconds)

    def delete_schedule(self, session_id: str) -> bool:
        return self.__scheduler.delete_schedule(session_id)
