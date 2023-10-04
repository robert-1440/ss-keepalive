from bean import BeanName
from bean.beans import inject
from instance import Instance
from notifier.notifier import Notifier
from push_notifier import PushNotifier
from scheduler import Scheduler
from secrets_repo import SecretsRepo
from session_repo import SessionRepo


@inject(bean_instances=(BeanName.SECRETS_REPO,
                        BeanName.SESSION_REPO,
                        BeanName.SCHEDULER,
                        BeanName.PUSH_NOTIFIER,
                        BeanName.NOTIFIER))
def init(secrets_repo: SecretsRepo,
         session_repo: SessionRepo,
         scheduler: Scheduler,
         push_notifier: PushNotifier,
         notifier: Notifier):
    return Instance(secrets_repo, session_repo, scheduler, push_notifier, notifier)
