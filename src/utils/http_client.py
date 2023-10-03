import json
import os
from enum import Enum
from typing import Dict, Any, Union, Iterable, Optional

import requests
from requests import Response, Session

from utils import GLOBAL_MUTEX


class HttpMethod(Enum):
    GET = 0,
    POST = 1,
    PATCH = 2
    PUT = 3,
    DELETE = 4


_MEDIA_TYPES = ["json", "x-www-form-urlencoded", "/text/html", "/image/jpeg", "/image/avif", "gzip", "*/*"]


class MediaType(Enum):
    JSON = 0
    X_WWW_FORM_URLENCODED = 1
    TEXT_HTML = 2
    IMAGE_JPEG = 3
    IMAGE_AVIF = 4
    GZIPPED = 5
    ALL = 6


class HttpResponse:
    def __init__(self, resp: Response = None,
                 status_code: int = None,
                 headers: Dict[str, str] = None,
                 body: str = None,
                 raw_body: bytes = None):
        if resp is not None:
            self.status_code = resp.status_code
            self.headers = resp.headers
            self.body = resp.text
            self.raw_body = resp._content
        else:
            self.status_code = status_code
            self.headers = headers
            self.body = body
            self.raw_body = raw_body

    def get_status_code(self):
        return self.status_code

    def get_body(self):
        return self.body

    def get_raw_body(self) -> bytes:
        return self.raw_body


class HttpRequest:
    def __init__(self, method: HttpMethod, url: str, headers: Dict[str, str] = None,
                 body: str = None):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body

    def _send(self, session: Session) -> Response:
        params = {}
        if self.headers is not None and len(self.headers) > 0:
            params['headers'] = self.headers
        if self.body is not None:
            params['data'] = self.body

        return session.request(self.method.name, self.url, **params)


class HttpException(Exception):
    def __init__(self, r: Response):
        self.response = r

    def get_status_code(self):
        return self.response.status_code

    def is_5xx(self):
        return 500 <= self.response.status_code < 600

    def get_body_as_string(self):
        return str(self.response.text)

    def get_headers(self):
        return self.response.headers

    def __str__(self):
        message = "{}: {}".format(self.response.status_code, str(self.response.text))
        body = self.get_body_as_string()
        if body is not None and len(body) > 0:
            message += f"\n{body}"
        return message

    def __repr__(self):
        return self.__str__()


class HttpClientException(HttpException):
    def __init__(self, r):
        super().__init__(r)


class HttpServerException(HttpException):
    def __init__(self, r):
        super().__init__(r)


def _create_session():
    ca_bundle = os.environ.get("CA_BUNDLE")
    sess = requests.Session()
    if ca_bundle is not None:
        sess.verify = ca_bundle
    return sess


class HttpClient:
    def __init__(self):
        self.__session = _create_session()

    def exchange(self, req: HttpRequest) -> HttpResponse:
        r = req._send(self.__session)
        _examine(r)
        return HttpResponse(r)


def _examine(r):
    if not r.ok:
        if r.status_code >= 500:
            raise HttpServerException(r)
        if r.status_code == 403:
            amzn = r.headers.get("x-amzn-ErrorType")
            if amzn is not None and amzn == "IncompleteSignatureException":
                r.status_code = 404
        raise HttpClientException(r)


def join_paths(*args) -> str:
    path = ""
    for arg in args:
        if len(path) > 0 and not path.endswith("/") and not arg.startswith("/"):
            path += "/"
        path += arg
    return path


def join_base_path(*args) -> str:
    path = join_paths(*args)
    if not path.endswith("/"):
        path += '/'
    return path


class RequestBuilder:
    def __init__(self, method: HttpMethod, uri: str):
        self.__method = method
        self.__uri = uri
        self.__headers = {}
        self.__body = None

    def body(self, body: Any):
        if self.__method in (HttpMethod.GET, HttpMethod.DELETE):
            raise ValueError(f"Body not allowed for {self.__method}")
        if isinstance(body, dict):
            body = json.dumps(body)
        self.__body = body
        return self

    def header(self, name: str, value: Union[str, Iterable[str]]):
        if not isinstance(value, str):
            if isinstance(value, Iterable):
                value = ", ".join(value)
        self.__headers[name] = value
        return self

    def authorization(self, token_type: str, token: str = None):
        value = token_type
        if token is not None:
            value += f" {token}"
        return self.header('Authorization', value)

    def accept(self, media_type: MediaType):
        return self.header("Accept", _MEDIA_TYPES[media_type.value])

    def content_type(self, media_type: Union[MediaType, str]):
        if self.__method in (HttpMethod.GET, HttpMethod.DELETE):
            raise ValueError(f"Content-Type not allowed for {self.__method.name}")
        if isinstance(media_type, str):
            value = media_type
        else:
            value = _MEDIA_TYPES[media_type.value]
        return self.header("Content-Type", value)

    def get_uri(self) -> str:
        return self.__uri

    def get_method(self) -> HttpMethod:
        return self.__method

    def get_body(self) -> Optional[str]:
        return self.__body

    def build(self, base_url: str = None) -> HttpRequest:
        if base_url is None:
            url = self.__uri
        else:
            url = join_paths(base_url, self.__uri)
        return HttpRequest(self.__method, url, self.__headers, self.__body)

    def send(self, client: HttpClient, base_url: str = None) -> HttpResponse:
        return client.exchange(self.build(base_url))


__DEFAULT_HTTP_CLIENT: Optional[HttpClient] = None


def get_default() -> HttpClient:
    global __DEFAULT_HTTP_CLIENT
    if __DEFAULT_HTTP_CLIENT is None:
        with GLOBAL_MUTEX:
            if __DEFAULT_HTTP_CLIENT is None:
                __DEFAULT_HTTP_CLIENT = HttpClient()
    return __DEFAULT_HTTP_CLIENT
