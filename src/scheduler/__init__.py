import abc


class Scheduler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_schedule(self, session_id: str, at_time: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_schedule(self, session_id: str, at_time: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_schedule(self, session_id: str):
        raise NotImplementedError()

