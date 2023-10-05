import json
import os
from traceback import print_exc
from typing import Any
import signal

from bean import BeanName
from bean.beans import inject
from instance import Instance
from internal import InternalEventProcessor
from request import HttpRequest, HttpException, Response
from utils import loghelper
from web import WebRequestProcessor, init_lambda

logger = loghelper.get_logger(__name__)

__SERVER_ERROR_RESPONSE = {'statusCode': 500, 'body': {
    'errorMessage': "Internal Server Error"
}}

init_lambda(logger)


@inject(bean_instances=(BeanName.INSTANCE, BeanName.WEB_ROUTER))
def __dispatch_web_request(event: dict, context: Any, instance: Instance, web_router: WebRequestProcessor):
    try:
        request = HttpRequest(event)
        logger.info(
            "Received Request:\n"
            f"    {request.method} {request.path}\n"
            f"    Source IP: {request.source_ip}"
        )

        if not instance.has_function_arn():
            logger.info(f"Invoked Function arn: {context.invoked_function_arn}")
            instance.set_function_arn(context.invoked_function_arn)
        return web_router.process(instance, request)
    except HttpException as ex:
        logger.error(f"Error: {ex}")
        resp_dict = ex.to_response()
    except Exception:
        print_exc()
        resp_dict = __SERVER_ERROR_RESPONSE
    return resp_dict


@inject(bean_instances=(BeanName.INSTANCE, BeanName.INTERNAL_ROUTER))
def __process_internal_event(event: dict, instance: Instance, router: InternalEventProcessor):
    return router.process(instance, event)


def handler(event: dict, context: Any):
    def wrapper():
        logger.info(f'Received event:\n {json.dumps(event, indent=True)}')

        internal_event = event.get('internalEvent')
        if internal_event is not None:
            return __process_internal_event(event)
        return __dispatch_web_request(event, context)

    r = wrapper()
    if r is not None:
        if isinstance(r, Response):
            r = r.to_dict()
        if isinstance(r, dict):
            r['isBase64Encoded'] = False
            r = json.dumps(r)
    return r
