from typing import Optional, Any

from aws.dynamodb import DynamoDb, PrimaryKeyViolationException, PreconditionFailedException
from session_repo import SessionRepo, Session

_SESSION_ID_PROPERTY = 'sessionId'

_TABLE_NAME = "SSKeepaliveSession"


class AwsSessionRepo(SessionRepo):
    def __init__(self, client: Any):
        self.__ddb = DynamoDb(client)

    def create_session(self, session: Session) -> bool:
        item = session.to_record()
        try:
            self.__ddb.put_item(_TABLE_NAME, item, [_SESSION_ID_PROPERTY])
        except PrimaryKeyViolationException:
            return False
        return True

    def extend_session(self, session_id: str, expire_at: int) -> bool:
        try:
            self.__ddb.update_item(_TABLE_NAME, keys={_SESSION_ID_PROPERTY: session_id},
                                   item={'expireTime': expire_at})
            return True
        except PreconditionFailedException:
            return False

    def find_session(self, session_id: str) -> Optional[Session]:
        item = self.__ddb.find_item(_TABLE_NAME, {_SESSION_ID_PROPERTY: session_id}, consistent=True)
        return Session.from_record(item) if item is not None else None

    def delete_session(self, session_id: str) -> bool:
        return self.__ddb.delete_item(_TABLE_NAME, keys={_SESSION_ID_PROPERTY: session_id})
