from typing import Dict, Any

from instance import Instance
from request import HttpRequest
from web import sessions, WebRequestProcessor
from web.lf import router

__MODULES = (sessions,)


class WebRequestProcessorImpl(WebRequestProcessor):
    def process(self, instance: Instance, request: HttpRequest) -> Dict[str, Any]:
        return router.process(instance, request)


def init():
    return WebRequestProcessorImpl()
