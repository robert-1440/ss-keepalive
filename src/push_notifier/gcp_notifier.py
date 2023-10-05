from threading import RLock
from types import ModuleType
from typing import Optional, Dict

from firebase_admin import App
from firebase_admin.credentials import Certificate
from firebase_admin.messaging import Message

from bean import Bean
from push_notifier import PushNotifier
from secrets_repo import GcpCredentials


class GcpPushNotifier(PushNotifier):
    def __init__(self,
                 gcp_creds_bean: Bean,
                 firebase_admin_bean: Bean,
                 cert_builder_bean: Bean
                 ):
        self.gcp_creds_bean = gcp_creds_bean
        self.firebase_admin_bean = firebase_admin_bean
        self.cert_builder_bean = cert_builder_bean
        self.messaging: Optional[ModuleType] = None
        self.app: Optional[App] = None
        self.mutex = RLock()

    def notify(self, token: str, data: Dict[str, str], dry_run: bool = False):
        messaging = self.__check_app()
        message = Message(
            data=data,
            token=token
        )
        messaging.send(message, dry_run=dry_run)

    def __obtain_app(self):
        creds: GcpCredentials = self.gcp_creds_bean.get_instance()
        firebase_admin = self.firebase_admin_bean.get_instance()
        self.messaging = firebase_admin.messaging
        builder = self.cert_builder_bean.get_instance()
        self.app = firebase_admin.initialize_app(builder(creds.content))

    def __check_app(self) -> ModuleType:
        if self.app is None:
            with self.mutex:
                if self.app is None:
                    self.__obtain_app()

        return self.messaging
