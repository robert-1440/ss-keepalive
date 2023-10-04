import functools
import os
import sys
from threading import RLock
from typing import Union, Callable, Any, Dict, Collection

import boto3

from bean import BeanName, Bean

BeanValue = Union[Callable, Any]


class _Boto3Loader:
    def __init__(self, service: str):
        self.service = service

    def invoke(self) -> Any:
        return boto3.client(self.service)


class _LazyLoader:
    def __init__(self, name: str,
                 bean_names: Union[Collection[BeanName], BeanName] = None,
                 tag_as_lazy: bool = True):
        if bean_names is not None and isinstance(bean_names, BeanName):
            bean_names = (bean_names,)
        self.name = name
        self.bean_names = bean_names
        self.init_function = None
        # Note: when tag as lazy is False, don't include it in load_all_lazy()
        # Should be used on beans that make callouts
        self.tag_as_lazy = tag_as_lazy

    def invoke(self) -> Any:
        if self.init_function is None:
            code = f"from bean.loaders import {self.name}\n\n"
            local_vars = {}
            exec(code, sys.modules[__name__].__dict__, local_vars)
            self.init_function = local_vars[self.name].__dict__['init']

        if self.bean_names is not None and len(self.bean_names) > 0:
            args = list(map(lambda n: get_bean_instance(n), self.bean_names))
        else:
            args = []
        return self.init_function(*args)


class _BeanImpl(Bean):
    def __init__(self, initializer: BeanValue):
        self.__initializer = initializer
        self.__override_initializer = None
        self.__initialized = False
        self.__value = None
        self.__mutex = RLock()
        self.__lazy = isinstance(initializer, _LazyLoader) and initializer.tag_as_lazy

    def __initialize(self):
        initializer = self.__override_initializer if self.__override_initializer else self.__initializer
        if isinstance(initializer, _LazyLoader):
            self.__value = initializer.invoke()
        elif isinstance(initializer, _Boto3Loader):
            self.__value = initializer.invoke()
        elif callable(initializer):
            self.__value = initializer()
        else:
            self.__value = initializer
        self.__initialized = True

    def set_initializer(self, value: Any):
        self.__override_initializer = value
        self.__initialized = False

    @property
    def lazy(self):
        return self.__lazy

    def reset(self):
        if self.__initialized:
            self.__value = None
            self.__initialized = False
            self.__override_initializer = None

    def get_instance(self):
        if not self.__initialized:
            with self.__mutex:
                if not self.__initialized:
                    self.__initialize()
        return self.__value


__BEANS: Dict[BeanName, _BeanImpl] = {
    BeanName.DYNAMODB: _BeanImpl(_LazyLoader('dynamodb')),
    BeanName.INSTANCE: _BeanImpl(_LazyLoader('instance')),
    BeanName.SCHEDULER_CLIENT: _BeanImpl(_Boto3Loader('scheduler')),
    BeanName.DYNAMODB_CLIENT: _BeanImpl(_Boto3Loader('dynamodb')),
    BeanName.SECRETS_MANAGER_CLIENT: _BeanImpl(_Boto3Loader('secretsmanager')),
    BeanName.SECRETS_REPO: _BeanImpl(_LazyLoader('secrets_repo')),
    BeanName.SESSION_REPO: _BeanImpl(_LazyLoader('session_repo')),
    BeanName.SCHEDULER: _BeanImpl(_LazyLoader('scheduler')),
    BeanName.WEB_ROUTER: _BeanImpl(_LazyLoader('web')),
    BeanName.INTERNAL_ROUTER: _BeanImpl(_LazyLoader('internal')),
    BeanName.GCP_CREDS: _BeanImpl(_LazyLoader('gcp_creds', tag_as_lazy=False)),
    BeanName.FIREBASE_ADMIN: _BeanImpl(_LazyLoader('firebase')),
    BeanName.PUSH_NOTIFIER: _BeanImpl(_LazyLoader('push_notifier')),
    BeanName.NOTIFIER: _BeanImpl(_LazyLoader('notifier')),
    BeanName.SNS_CLIENT: _BeanImpl(_Boto3Loader('sns'))
}


def override_bean(name: BeanName, value: BeanValue):
    """
    This should be used for testing only.

    :param name: the bean name.
    :param value: the value for the bean.
    """
    assert isinstance(name, BeanName)
    b = __BEANS[name]
    b.set_initializer(value)


def reset():
    """
    Use during unit tests only!
    """
    for bean in __BEANS.values():
        bean.reset()


def get_bean(name: BeanName) -> Bean:
    return __BEANS[name]


def get_bean_instance(name: BeanName) -> Any:
    b = __BEANS.get(name)
    if b is None:
        raise ValueError(f"No bean registered for {name.name}")
    return b.get_instance()


def _check_it(thing: Any):
    if thing is not None:
        if not isinstance(thing, Collection):
            return (thing,)
        if len(thing) == 0:
            return None
    return thing


def inject(bean_instances: Union[BeanName, Collection[BeanName]] = None,
           beans: Union[BeanName, Collection[BeanName]] = None):
    bean_instances = _check_it(bean_instances)
    beans = _check_it(beans)

    if bean_instances is not None and len(bean_instances) == 0:
        bean_instances = None
    if beans is not None and len(beans) == 0:
        beans = None

    def decorator(wrapped_function):
        @functools.wraps(wrapped_function)
        def _inner_wrapper(*args):
            args_copy = list(args)
            if bean_instances is not None:
                for bv in bean_instances:
                    args_copy.append(get_bean_instance(bv))
            if beans is not None:
                for bv in beans:
                    args_copy.append(get_bean(bv))
            return wrapped_function(*args_copy)

        return _inner_wrapper

    return decorator


def load_all_lazy():
    """
    Used to load all the lazy beans.  This should be called when archiving only.
    """
    impl: _BeanImpl
    for impl in filter(lambda b: b.lazy, __BEANS.values()):
        impl.get_instance()
