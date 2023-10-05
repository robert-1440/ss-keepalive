import re

from request import BadRequestException

__SESSION_ID_REGX = re.compile(r"^[a-zA-Z0-9-]+$")


def validate_session_id(session_id: str):
    if not re.match(__SESSION_ID_REGX, session_id):
        raise BadRequestException(f"Invalid session id: '{session_id}', must be alpha-numeric.")
