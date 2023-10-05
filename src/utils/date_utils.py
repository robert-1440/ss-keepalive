import time
from datetime import datetime


def get_system_time_in_millis():
    return time.time_ns() // 1_000_000


def get_system_time_in_seconds():
    return get_system_time_in_millis() // 1000


def calc_expire_time_in_epoch_seconds(seconds_in_future: int, from_time: datetime = None):
    if from_time is None:
        from_time = datetime.utcnow()
    stamp = int(from_time.timestamp() * 1000)
    return ((stamp + 500) // 1000) + seconds_in_future
