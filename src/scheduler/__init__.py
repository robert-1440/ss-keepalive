import abc


class Scheduler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_schedule(self, function_arn: str, session_id: str, seconds_interval: int) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def update_schedule(self, function_arn: str, session_id: str, seconds_interval: int) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_schedule(self, session_id: str) -> bool:
        raise NotImplementedError()

