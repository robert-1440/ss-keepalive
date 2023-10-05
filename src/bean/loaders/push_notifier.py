from bean import BeanName, Bean
from bean.beans import inject
from push_notifier.gcp_notifier import GcpPushNotifier


@inject(beans=(BeanName.GCP_CREDS, BeanName.FIREBASE_ADMIN, BeanName.GCP_CERT_BUILDER))
def init(gcp_creds_bean: Bean, firebase_admin_bean: Bean, cert_builder_bean: Bean):
    return GcpPushNotifier(gcp_creds_bean, firebase_admin_bean, cert_builder_bean)
