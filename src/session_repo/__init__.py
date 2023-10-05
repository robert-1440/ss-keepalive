import abc
from typing import Optional

from utils.date_utils import get_system_time_in_seconds


class Session:
    def __init__(self,
                 session_id: str,
                 fcm_device_token: str,
                 interval_seconds: int,
                 expire_time: Optional[int] = None,
                 last_modified: Optional[int] = None,
                 state_counter: int = 0):
        self.session_id = session_id
        self.fcm_device_token = fcm_device_token
        self.interval_seconds = interval_seconds
        self.expire_time = expire_time
        self.last_modified = last_modified
        self.state_counter = state_counter

    def __eq__(self, other):
        return isinstance(other, Session) and \
            self.session_id == other.session_id and \
            self.fcm_device_token == other.fcm_device_token and \
            self.interval_seconds == other.interval_seconds and \
            self.expire_time == other.expire_time and \
            self.last_modified == other.last_modified and \
            self.state_counter == other.state_counter

    def to_record(self):
        return {
            'sessionId': self.session_id,
            'fcmDeviceToken': self.fcm_device_token,
            'intervalSeconds': self.interval_seconds,
            'expireTime': self.expire_time,
            'lastModified': self.last_modified,
            'stateCounter': self.state_counter
        }

    @classmethod
    def from_record(cls, record: dict):
        return Session(
            record['sessionId'],
            record['fcmDeviceToken'],
            record['intervalSeconds'],
            record['expireTime'],
            record['lastModified'],
            record['stateCounter']
        )

    def is_expired(self) -> bool:
        return get_system_time_in_seconds() >= self.expire_time


class SessionRepo(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def create_session(self, session: Session, ttl_seconds: int) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def extend_session(self, session: Session, seconds_in_future: int) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_session(self, session_id: str) -> Optional[Session]:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError()
