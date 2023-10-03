import time


def get_system_time_in_millis():
    return time.time_ns() // 1_000_000


def get_system_time_in_seconds():
    return get_system_time_in_millis() // 1000
