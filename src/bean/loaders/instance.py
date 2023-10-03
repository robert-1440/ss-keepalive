from bean import BeanName
from bean.beans import inject
from instance import Instance
from secrets_repo import SecretsRepo
from session_repo import SessionRepo


@inject(bean_instances=(BeanName.SECRETS_REPO, BeanName.SESSION_REPO))
def init(secrets_repo: SecretsRepo, session_repo: SessionRepo):
    return Instance(secrets_repo, session_repo)
