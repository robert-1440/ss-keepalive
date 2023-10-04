from bean import BeanName
from bean.beans import inject
from secrets_repo import SecretsRepo, GcpCredentials


@inject(bean_instances=BeanName.SECRETS_REPO)
def init(repo: SecretsRepo) -> GcpCredentials:
    creds = repo.find_gcp_credentials()
    if creds is None:
        raise ValueError("Cannot find GCP credentials.")
    return creds
