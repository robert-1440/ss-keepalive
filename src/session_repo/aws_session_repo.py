from typing import Optional, Any

from aws.dynamodb import DynamoDb, PrimaryKeyViolationException, PreconditionFailedException
from session_repo import SessionRepo, Session
from datetime import datetime

from utils import date_utils
from utils.date_utils import get_system_time_in_millis

_SESSION_ID_PROPERTY = 'sessionId'

_TABLE_NAME = "SSKeepaliveSession"


class AwsSessionRepo(SessionRepo):
    def __init__(self, client: Any):
        self.__ddb = DynamoDb(client)

    def create_session(self, session: Session, ttl_seconds: int) -> bool:
        item = session.to_record()
        lm = item.get('lastModified')
        if lm is None:
            item['lastModified'] = get_system_time_in_millis()
        et = item.get('expireTime')
        if et is None:
            item['expireTime'] = date_utils.calc_expire_time_in_epoch_seconds(ttl_seconds)

        try:
            self.__ddb.put_item(_TABLE_NAME, item, [_SESSION_ID_PROPERTY])
        except PrimaryKeyViolationException:
            return False
        return True

    def extend_session(self, session: Session, seconds_in_future: int) -> bool:
        try:
            expire_at = date_utils.calc_expire_time_in_epoch_seconds(seconds_in_future)
            state_counter = session.state_counter + 1
            self.__ddb.update_item(_TABLE_NAME, keys={_SESSION_ID_PROPERTY: session.session_id},
                                   item={
                                       'stateCounter': state_counter,
                                       'expireTime': expire_at,
                                       'lastModified': get_system_time_in_millis()
                                   },
                                   condition={'stateCounter': session.state_counter})
            return True
        except PreconditionFailedException:
            return False

    def find_session(self, session_id: str) -> Optional[Session]:
        item = self.__ddb.find_item(_TABLE_NAME, {_SESSION_ID_PROPERTY: session_id}, consistent=True)
        return Session.from_record(item) if item is not None else None

    def delete_session(self, session_id: str) -> bool:
        return self.__ddb.delete_item(_TABLE_NAME, keys={_SESSION_ID_PROPERTY: session_id})
