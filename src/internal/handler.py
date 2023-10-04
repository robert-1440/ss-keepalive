from typing import Any, Dict
from instance import Instance
from internal import InternalEventProcessor
from request import get_required_parameter


class InternalEventProcessorImpl(InternalEventProcessor):
    def process(self, instance: Instance, event: Dict[str, Any]) -> Dict[str, Any]:
        internal_event: dict = get_required_parameter(event, 'internalEvent', dict)
        event_type = get_required_parameter(internal_event, 'type', str)
        raise NotImplementedError()
