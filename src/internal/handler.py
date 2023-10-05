from typing import Any, Dict, Optional
from instance import Instance
from internal import InternalEventProcessor
from request import get_required_parameter
from utils import loghelper

logger = loghelper.get_logger(__name__)


class InternalEventProcessorImpl(InternalEventProcessor):
    def process(self, instance: Instance, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        internal_event: dict = get_required_parameter(event, 'internalEvent', dict)
        event_type = get_required_parameter(internal_event, 'type', str)
        if event_type == 'keepalive':
            self.keep_alive(instance, internal_event)
            return None
        logger.error(f"Unrecognized event type: {event_type}")
        return None

    @staticmethod
    def keep_alive(instance: Instance, event: Dict[str, Any]):
        session_id = event.get('sessionId')
        if session_id is None:
            logger.error(f"sessionId not found in event: {event}")
            return

        session = instance.find_session(session_id)
        if session is None or session.is_expired():
            state = "gone" if session is None else "expired"
            logger.info(f"Session {session_id} is {state}, deleting schedule.")
            instance.delete_schedule(session_id)
        else:
            logger.info(f"Sending push notification for sessionId {session_id} ...")
            instance.send_push_notification(session.fcm_device_token, session_id)
