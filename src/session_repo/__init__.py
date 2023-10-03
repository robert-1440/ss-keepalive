import abc
from typing import Optional


class Session:
    def __init__(self,
                 session_id: str,
                 fcm_device_token: str,
                 interval_seconds: int,
                 expire_time: int):
        self.session_id = session_id
        self.fcm_device_token = fcm_device_token
        self.interval_seconds = interval_seconds
        self.expire_time = expire_time

    def to_record(self):
        return {
            'sessionId': self.session_id,
            'fcmDeviceToken': self.fcm_device_token,
            'intervalSeconds': self.interval_seconds,
            'expireTime': self.expire_time
        }

    @classmethod
    def from_record(cls, record: dict):
        return Session(
            record['sessionId'],
            record['fcmDeviceToken'],
            record['intervalSeconds'],
            record['expireTime']
        )


class SessionRepo(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def create_session(self, session: Session) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def extend_session(self, session_id: str, expire_at: int) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_session(self, session_id: str) -> Optional[Session]:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError()
