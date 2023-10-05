from datetime import datetime
from typing import Optional, Dict

from botomocks import BaseMockClient, assert_empty, raise_conflict_exception, KeyId, raise_not_found
from request import get_required_parameter, get_parameter


class Target:
    def __init__(self, node: dict):
        node = dict(node)
        self.role_arn = get_required_parameter(node, "RoleArn", str, remove=True)
        self.arn = get_required_parameter(node, "Arn", str, remove=True)
        self.input = get_required_parameter(node, "Input", str, remove=True)
        assert_empty(node)


class Schedule:
    name: str
    group_name: Optional[str]
    schedule_expression: str
    start_date: Optional[datetime]
    target: Target
    flexible_time_window: Dict[str, str]

    def __init__(self, node: dict):
        node = dict(node)
        self.name = get_required_parameter(node, "Name", str, remove=True)
        self.group_name = get_parameter(node, "GroupName", str, remove=True)
        self.schedule_expression = get_required_parameter(node, "ScheduleExpression", str, remove=True)
        self.target = Target(get_required_parameter(node, "Target", dict, remove=True))
        self.start_date = get_parameter(node, "StartDate", datetime, remove=True)
        self.flexible_time_window = get_required_parameter(node, "FlexibleTimeWindow", dict, remove=True)

        assert_empty(node)


class MockSchedulerClient(BaseMockClient):

    def __init__(self):
        super().__init__()
        self.schedules: Dict[KeyId, Schedule] = {}
        self.__raise_exists_on_next_create = False

    def set_raise_exists_on_next_create(self):
        self.__raise_exists_on_next_create = True

    def find_schedule_by_session(self, group_name: str, session_id: str):
        name = f"ss-keepalive-{session_id}"
        key_id = KeyId(group_name, name)
        return self.schedules.get(key_id)

    def create_schedule(self, **kwargs):
        schedule = Schedule(kwargs)
        key_id = KeyId(schedule.group_name or "default", schedule.name)
        if key_id in self.schedules or self.__raise_exists_on_next_create:
            self.__raise_exists_on_next_create = False
            raise_conflict_exception("CreateSchedule",
                                     f"Schedule with name {schedule.name} already exists.")
        self.schedules[key_id] = schedule

    def delete_schedule(self, **kwargs):
        group_name = kwargs.pop("GroupName", "default")
        name = kwargs.pop("Name")
        assert_empty(kwargs)
        key_id = KeyId(group_name, name)
        removed = self.schedules.pop(key_id, None)
        if removed is None:
            raise_not_found("Schedule not found")

    def create_paginator(self, operation_name: str):
        pass
