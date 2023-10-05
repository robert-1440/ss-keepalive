import abc
import os
import signal
from logging import Logger
from typing import Dict, Any

from instance import Instance
from request import HttpRequest
from utils.date_utils import get_system_time_in_seconds

ROOT_URL = "/ss/"


class WebRequestProcessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def process(self, instance: Instance, request: HttpRequest) -> Dict[str, Any]:
        raise NotImplementedError()


def init_lambda(logger: Logger):
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None:
        start_time = get_system_time_in_seconds()
        # Set up for informational purposes, if we are actually in a Lambda
        old_sig = signal.getsignal(signal.SIGTERM)

        def _goodbye_handler(signum, frame):
            elapsed = get_system_time_in_seconds() - start_time
            logger.info(f"Lambda exiting, seconds up: {elapsed}.")
            signal.signal(signum, old_sig)
            signal.raise_signal(signum)

        signal.signal(signal.SIGTERM, _goodbye_handler)
