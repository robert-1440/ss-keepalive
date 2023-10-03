from typing import Any

from scheduler import Scheduler


class AwsScheduler(Scheduler):
    def __init__(self, client: Any):
        self.client = client

    def create_schedule(self, session_id: str, at_time: int):
        pass

    def update_schedule(self, session_id: str, at_time: int):
        pass

    def delete_schedule(self, session_id: str):
        pass
