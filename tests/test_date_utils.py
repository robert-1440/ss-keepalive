from better_test_case import BetterTestCase
from datetime import datetime

from utils import date_utils


def _get_time(minute: int, second: int, millis: int) -> datetime:
    now = datetime.utcnow()
    micros = millis * 1000
    return datetime(now.year, now.month, now.day, now.hour, minute, second, micros)


def _to_datetime(seconds: int) -> datetime:
    return datetime.utcfromtimestamp(seconds)


class DateTests(BetterTestCase):

    def test_calc_expire_time_in_epoch_seconds(self):
        self._execute_test(15, 0, 0, 30, 15, 30)
        self._execute_test(15, 0, 499, 30, 15, 30)
        self._execute_test(15, 0, 500, 30, 15, 31)

        self._execute_test(15, 0, 0, 60, 16, 00)

    def _execute_test(self, minute: int, second: int, millis: int, seconds_to_add: int,
                      expected_minute: int, expected_seconds: int):
        t = _get_time(minute, second, millis)
        exp = date_utils.calc_expire_time_in_epoch_seconds(seconds_to_add, t)
        d = _to_datetime(exp)
        self.assertEqual(expected_minute, d.minute, msg="Minute")
        self.assertEqual(expected_seconds, d.second, msg="Second")
