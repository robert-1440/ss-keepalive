import os
import uuid

from bean import beans, BeanName
from instance import Instance
from session_repo import Session
from utils.date_utils import get_system_time_in_seconds

os.environ['AWS_PROFILE'] = 'MyRepStudio'
os.environ['SS_KEEPALIVE_ERROR_TOPIC_ARN'] = 'some.arn'
os.environ['SS_KEEPALIVE_SCHEDULE_GROUP'] = 'NotificationGroup'
os.environ[
    'SS_KEEPALIVE_SCHEDULE_GROUP_ROLE_ARN'] = 'arn:aws:iam::433933949595:role/terraform-20231004215941515800000001'

_TOKEN = "c-0F2zOcQJioxzCg2g8odH:APA91bHPT6UeqRfpCTBIICcLwxA6UuGNfXd_CG7Xj-8_Z3XBUAzCF8fGFukaxDSybwCbde7fu6hKLm_gFOwIGmBiGcENGmrY0RzMcEyHXrB2NDWYnMgaeYwC9AFfyHp617Z8iuc3QGiG"

instance: Instance = beans.get_bean_instance(BeanName.INSTANCE)
# instance.push_notification(_TOKEN, "some-id")


arn = "arn:aws:lambda:us-west-1:433933949595:function:ssKeepaliveService"

session_id = '727a6ed5-5bdf-4ed0-8bae-ecb8e20aef46'

#session_id = str(uuid.uuid4())
expire_time = get_system_time_in_seconds() + 120

session = Session(
    session_id,
    _TOKEN,30,
    expire_time
)

result = instance.create_session(session)
instance.delete_schedule(session_id)
# instance.create_schedule(arn, session_id, 120)



