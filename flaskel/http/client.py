import flask
from requests import auth
from requests import exceptions as http_exc
from requests import request as send_request

from flaskel import flaskel
from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.faker.logger import FakeLogger
from flaskel.utils.uuid import get_uuid
from . import httpcode
from .httpdumper import FlaskelHTTPDumper
from .httpdumper import LazyHTTPDumper

HTTPStatusError = (http_exc.HTTPError,)
NetworkError = (http_exc.ConnectionError, http_exc.Timeout)
all_errors = (*HTTPStatusError, *NetworkError)

cap = flaskel.cap
request: "flaskel.Request" = flask.request  # type: ignore


class HTTPTokenAuth(auth.AuthBase):
    def __init__(self, token):
        """

        :param token:
        """
        self.token = token

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        return self.token == getattr(other, "token", None)  # pragma: no cover

    def __ne__(self, other):
        """

        :param other:
        :return:
        """
        return not self == other  # pragma: no cover

    def __call__(self, r):
        """

        :param r:
        :return:
        """
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class HTTPBase(LazyHTTPDumper):
    def __init__(self, dump_body=False, timeout=10, raise_on_exc=False, logger=None):
        """

        :param dump_body:
        :param timeout:
        :param raise_on_exc:
        :param logger:
        """
        self._dump_body = self._normalize_dump_flag(dump_body)
        self._timeout = timeout
        self._raise_on_exc = raise_on_exc
        self._logger = logger or FakeLogger()

    @staticmethod
    def _normalize_dump_flag(dump_body):
        if isinstance(dump_body, bool):
            return dump_body, dump_body
        if not dump_body:
            return False, False
        return dump_body

    def request(self, uri, dump_body=None, **kwargs):
        """

        :param uri:
        :param dump_body:
        :param kwargs:
        """
        raise NotImplementedError  # pragma: no cover


class HTTPClient(HTTPBase):
    def __init__(self, endpoint, token=None, username=None, password=None, **kwargs):
        """

        :param endpoint:
        :param token:
        :param username:
        :param password:
        """
        super().__init__(**kwargs)
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._token = token

    def get_auth(self):
        """

        :return:
        """
        if self._username and self._password:
            return auth.HTTPBasicAuth(self._username, self._password)
        if self._token:
            return HTTPTokenAuth(self._token)
        return None

    def normalize_url(self, url):
        if url.startswith("http"):
            return url

        return f"{self._endpoint}/{url.lstrip('/')}"

    @staticmethod
    def prepare_response(
        body=None, status=httpcode.SUCCESS, headers=None, exception=None
    ):
        return ObjectDict(
            body=body or {}, status=status, headers=headers or {}, exception=exception
        )

    def request(
        self,
        uri,
        method="GET",
        raise_on_exc=False,
        dump_body=None,
        chunk_size=None,
        decode_unicode=False,
        **kwargs,
    ):
        """

        :param uri:
        :param method:
        :param raise_on_exc:
        :param dump_body:
        :param chunk_size:
        :param decode_unicode:
        :param kwargs:
        :return:
        """
        kwargs["auth"] = self.get_auth()
        if dump_body is None:
            dump_body = self._dump_body
        else:
            dump_body = self._normalize_dump_flag(dump_body)
        if kwargs.get("stream") is True:  # if stream not dump response body
            dump_body = (dump_body[0], False)

        try:
            kwargs.setdefault("timeout", self._timeout)
            url = self.normalize_url(uri)
            req = ObjectDict(method=method, url=url, **kwargs)
            self._logger.info("%s", self.dump_request(req, dump_body[0]))
            response = send_request(method, self.normalize_url(uri), **kwargs)
        except NetworkError as exc:
            self._logger.exception(exc)
            if raise_on_exc or self._raise_on_exc:
                raise  # pragma: no cover

            return self.prepare_response(
                status=httpcode.SERVICE_UNAVAILABLE, exception=exc
            )

        log_resp = self.dump_response(response, dump_body[1])
        try:
            response.raise_for_status()
            self._logger.info("%s", log_resp)
        except HTTPStatusError as exc:
            self._logger.warning("%s", log_resp)
            response = exc.response
            if raise_on_exc or self._raise_on_exc:
                raise

        if kwargs.get("stream") is True:
            body = response.iter_content(chunk_size, decode_unicode)
        elif "json" in (response.headers.get("Content-Type") or ""):
            body = response.json()
        else:
            body = response.text

        return self.prepare_response(
            body=body, status=response.status_code, headers=dict(response.headers)
        )

    def get(self, uri, **kwargs):
        return self.request(uri, **kwargs)

    def post(self, uri, **kwargs):
        return self.request(uri, method="POST", **kwargs)

    def put(self, uri, **kwargs):
        return self.request(uri, method="PUT", **kwargs)

    def patch(self, uri, **kwargs):
        return self.request(uri, method="PATCH", **kwargs)

    def delete(self, uri, **kwargs):
        return self.request(uri, method="DELETE", **kwargs)

    def options(self, uri, **kwargs):
        return self.request(uri, method="OPTIONS", **kwargs)

    def head(self, uri, **kwargs):
        return self.request(uri, method="HEAD", **kwargs)


class JsonRPCClient(HTTPClient):
    def __init__(self, endpoint, uri, version="2.0", **kwargs):
        """

        :param endpoint:
        :param uri:
        :param version:
        """
        super().__init__(endpoint, raise_on_exc=True, **kwargs)
        self._uri = uri
        self._version = version
        self._request_id = None

    @property
    def request_id(self):
        """

        :return:
        """
        return self._request_id

    def request(self, method, request_id=None, **kwargs):
        """

        :param method:
        :param request_id:
        :param kwargs:
        :return:
        """
        self._request_id = request_id or get_uuid()
        return self._request(method, **kwargs)

    def notification(self, method, **kwargs):
        """

        :param method:
        :param kwargs:
        :return:
        """
        self._request_id = None
        return self._request(method, **kwargs)

    def _request(self, method, params=None, **kwargs):
        """

        :param method:
        :param params:
        :param kwargs:
        :return:
        """
        resp = super().request(
            self._uri,
            method="POST",
            json=dict(
                jsonrpc=self._version,
                method=method,
                params=params or {},
                id=self._request_id,
            ),
            **kwargs,
        )

        return resp.body or ObjectDict()


class FlaskelHttp(FlaskelHTTPDumper, HTTPClient):
    def __init__(self, endpoint, *args, **kwargs):
        kwargs.setdefault("logger", cap.logger)
        super().__init__(endpoint, *args, **kwargs)
        self._timeout = cap.config.HTTP_TIMEOUT or self._timeout

    def request(self, uri, **kwargs):
        if request.id:
            if not kwargs.get("headers"):
                kwargs["headers"] = {}
            kwargs["headers"][cap.config.REQUEST_ID_HEADER] = request.id

        kwargs.setdefault("verify", cap.config.HTTP_SSL_VERIFY)
        return super().request(uri, **kwargs)


class FlaskelJsonRPC(FlaskelHttp, JsonRPCClient):  # type: ignore
    pass
