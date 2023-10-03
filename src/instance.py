from secrets_repo import SecretsRepo
from session_repo import SessionRepo


class Instance:
    def __init__(self, secrets_repo: SecretsRepo,
                 session_repo: SessionRepo):
        self.secrets_repo = secrets_repo
        self.session_repo = session_repo
