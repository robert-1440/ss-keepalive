from instance import Instance
from request import HttpRequest
from web import ROOT_URL
from web.lf.resource import Resource
from web.lf.router import Method

sessions = Resource(ROOT_URL, "sessions")


@sessions.route("",
                response_codes=(201, 400, 409),
                method=Method.POST)
def create_session(instance: Instance,
                   request: HttpRequest):
    raise NotImplementedError()


@sessions.route("{sessionId}/actions/keepalive",
                response_codes=(204,),
                method=Method.POST)
def keep_session_alive(instance: Instance, request: HttpRequest, sessionId: str):
    raise NotImplementedError()


@sessions.route("{sessionId}",
                response_codes=(204,),
                method=Method.DELETE)
def delete_session(instance: Instance, sessionId: str):
    raise NotImplementedError()
