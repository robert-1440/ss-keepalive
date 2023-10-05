import json
from datetime import datetime, timedelta
from typing import Any, Dict

from aws import is_not_found_exception, is_conflict_exception
from scheduler import Scheduler

_FLEX_WINDOW = {"Mode": "OFF"}


def _format_time(seconds: int) -> str:
    t = datetime.utcnow() + timedelta(seconds=seconds)
    return f"at({t.year}-{t.month:02d}-{t.day:02d}T{t.hour:02d}:{t.minute:02d}:{t.second:02d})"


def _format_rate(minutes: int) -> str:
    return f"rate({minutes} minutes)"


class AwsScheduler(Scheduler):
    def __init__(self, client: Any, group_name: str, role_arn: str):
        self.client = client
        self.group_name = group_name
        self.role_arn = role_arn

    def _build_params(self, function_arn: str, session_id: str, seconds_interval: int) -> Dict[str, Any]:
        assert seconds_interval > 0
        # We can only specify minutes :(
        minutes = seconds_interval // 60
        if seconds_interval % 60 > 0:
            minutes += 1
        start_dt = datetime.utcnow() + timedelta(minutes=minutes)

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
            'ScheduleExpression': _format_rate(minutes),
            'Target': target,
            'StartDate': start_dt,
            'FlexibleTimeWindow': _FLEX_WINDOW
        }

    def create_schedule(self, function_arn: str, session_id: str, seconds_interval: int):
        params = self._build_params(function_arn, session_id, seconds_interval)
        try:
            self.client.create_schedule(**params)
        except Exception as ex:
            if is_conflict_exception(ex):
                return False
            raise ex
        return True

    def update_schedule(self, function_arn: str, session_id: str, seconds_interval: int):
        params = self._build_params(function_arn, session_id, seconds_interval)
        self.client.update_schedule(**params)
        return True

    def delete_schedule(self, session_id: str):
        name = f"ss-keepalive-{session_id}"
        try:
            self.client.delete_schedule(Name=name, GroupName=self.group_name)
            return True
        except Exception as ex:
            if is_not_found_exception(ex):
                return False
            raise ex
