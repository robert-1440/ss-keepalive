import json
from datetime import datetime, timedelta
from typing import Any, Dict

from scheduler import Scheduler

_FLEX_WINDOW = {"Mode": "OFF"}


def _format_time(seconds: int) -> str:
    t = datetime.utcnow() + timedelta(seconds=seconds)
    return f"at({t.year}-{t.month:02d}-{t.day:02d}T{t.hour:02d}:{t.minute:02d}:{t.second:02d})"


class AwsScheduler(Scheduler):
    def __init__(self, client: Any, group_name: str, role_arn: str):
        self.client = client
        self.group_name = group_name
        self.role_arn = role_arn

    def _build_params(self, function_arn: str, session_id: str, seconds_in_future: int) -> Dict[str, Any]:
        name = f"ss-keepalive-{session_id}"
        payload = {
            'internalEvent': {
                'type': 'keepalive',
                'sessionId': session_id
            }
        }
        target = {
            'RoleArn': self.role_arn,
            'Arn': function_arn,
            'Input': json.dumps(payload)
        }

        return {
            'Name': name,
            'GroupName': self.group_name,
            'ScheduleExpression': _format_time(seconds_in_future),
            'Target': target,
            'FlexibleTimeWindow': _FLEX_WINDOW
        }

    def create_schedule(self, function_arn: str, session_id: str, seconds_in_future: int):
        params = self._build_params(function_arn, session_id, seconds_in_future)
        print(params['ScheduleExpression'])
        self.client.create_schedule(**params)
        return True

    def update_schedule(self, function_arn: str, session_id: str, seconds_in_future: int):
        params = self._build_params(function_arn, session_id, seconds_in_future)
        self.client.update_schedule(**params)
        return True

    def delete_schedule(self, session_id: str):
        name = f"ss-keepalive-{session_id}"
        self.client.delete_schedule(Name=name, GroupName=self.group_name)
        return True
