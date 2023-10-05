from instance import Instance
from request import HttpRequest, from_json, get_required_parameter, assert_empty, BadRequestException, \
    EntityExistsException, Response, NotFoundException, GoneException
from session_repo import Session
from utils import loghelper
from utils.validation_utils import validate_session_id
from web import ROOT_URL
from web.lf.resource import Resource
from web.lf.router import Method

sessions = Resource(ROOT_URL, "sessions")

logger = loghelper.get_logger(__name__)


@sessions.route("",
                response_codes=(204, 400, 409),
                method=Method.POST)
def create_session(instance: Instance,
                   request: HttpRequest):
    body = from_json(request.body)
    session_id = get_required_parameter(body, "sessionId", str, remove=True)
    fcm_token = get_required_parameter(body, "fcmToken", str, remove=True)
    interval: int = get_required_parameter(body, "intervalMinutes", int, remove=True)
    assert_empty(body)

    validate_session_id(session_id)

    if interval < 1 or interval > 1440:
        raise BadRequestException(f"Invalid intervalMinutes: {interval}, must be between 1 and 1440.")

    interval *= 60
    message = instance.test_push_notification(fcm_token)
    if message is not None:
        raise BadRequestException(f"Invalid fcmToken: {message}.")

    session = Session(
        session_id,
        fcm_token,
        interval
    )

    if not instance.create_session(session):
        raise EntityExistsException(f"Session with id {session_id} already exists.")
    good = False
    try:
        good = instance.create_schedule(session_id, interval)
        if not good:
            logger.error(f"Schedule for session id {session_id} already exists.")
            raise EntityExistsException("Schedule already exists.")
    finally:
        if not good:
            instance.delete_session(session_id)

    return Response.no_content()


@sessions.route("{sessionId}/actions/keepalive",
                response_codes=(204, 410),
                method=Method.POST)
def keep_session_alive(instance: Instance, request: HttpRequest, sessionId: str):
    session = instance.find_session(sessionId)
    if session is None:
        raise NotFoundException(f"Session with id {sessionId} does not exist.")
    request.assert_empty_body()

    instance.extend_session(session)
    return Response.no_content()


@sessions.route("{sessionId}",
                response_codes=(204,),
                method=Method.DELETE)
def delete_session(instance: Instance, sessionId: str):
    session = instance.find_session(sessionId)
    if session is None:
        raise NotFoundException(f"Session with id {sessionId} does not exist.")
    instance.delete_session(sessionId)
    instance.delete_schedule(sessionId)
    return Response.no_content()
