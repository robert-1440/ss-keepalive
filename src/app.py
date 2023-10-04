import json
from traceback import print_exc
from typing import Any

from bean import BeanName
from bean.beans import inject
from instance import Instance
from request import HttpRequest, HttpException
from utils import loghelper
from web import WebRequestProcessor

logger = loghelper.get_logger(__name__)

__SERVER_ERROR_RESPONSE = {'statusCode': 500, 'body': {
    'errorMessage': "Internal Server Error"
}}


@inject(bean_instances=(BeanName.INSTANCE, BeanName.WEB_ROUTER))
def __dispatch_web_request(event: dict, instance: Instance, web_router: WebRequestProcessor):
    try:
        request = HttpRequest(event)
        return web_router.process(instance, request)
    except HttpException as ex:
        logger.error(f"Error: {ex}")
        resp_dict = ex.to_response()
    except Exception:
        print_exc()
        resp_dict = __SERVER_ERROR_RESPONSE
    return resp_dict


@inject(bean_instances=BeanName.INSTANCE)
def __process_internal_event(event: dict, instance: Instance):
    pass


def handler(event: dict, context: Any):
    logger.info(f'Received event:\n {json.dumps(event, indent=True)}')

    internal_event = event.get('internalEvent')
    if internal_event is not None:
        return __process_internal_event(event)
    return __dispatch_web_request(event)
