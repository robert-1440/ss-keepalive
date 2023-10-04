import abc


class Notifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_error(self, subject: str, message: str):
        raise NotImplementedError()
