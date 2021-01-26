import flask
from requests import auth, exceptions as http_exc, request as send_request

from flaskel import cap
from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.faker import FakeLogger
from flaskel.utils.uuid import get_uuid
from . import httpcode
from .httpdumper import FlaskelHTTPDumper, HTTPDumper


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
        return self.token == getattr(other, 'token', None)  # pragma: no cover

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
        r.headers['Authorization'] = f"Bearer {self.token}"
        return r


class HTTPBase(HTTPDumper):
    def __init__(self, dump_body=False, timeout=10, raise_on_exc=False, logger=None):
        """

        :param dump_body:
        :param timeout:
        :param raise_on_exc:
        :param logger:
        """
        self._dump_body = dump_body
        self._timeout = timeout
        self._raise_on_exc = raise_on_exc
        self._logger = logger or FakeLogger()

    def request(self, uri, dump_body=None, **kwargs):
        """

        :param uri:
        :param dump_body:
        :param kwargs:
        """
        raise NotImplemented  # pragma: no cover


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

    def normalize_url(self, url):
        if url.startswith('http'):
            return url

        return f"{self._endpoint}/{url.rstrip('/')}"

    def request(self, uri, method='GET', raise_on_exc=False,
                dump_body=None, chunk_size=None, decode_unicode=False, **kwargs):
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
        kwargs['auth'] = self.get_auth()
        if dump_body is None:
            dump_body = self._dump_body
        if kwargs.get('stream') is True:
            dump_body = False

        try:
            kwargs.setdefault('timeout', self._timeout)
            response = send_request(method, self.normalize_url(uri), **kwargs)
            self._logger.info(self.dump_request(response.request, dump_body))
        except (http_exc.ConnectionError, http_exc.Timeout) as exc:
            self._logger.exception(exc)
            if raise_on_exc or self._raise_on_exc:
                raise  # pragma: no cover

            return ObjectDict(
                body={},
                status=httpcode.SERVICE_UNAVAILABLE,
                headers={},
                exception=exc
            )

        try:
            response.raise_for_status()
        except http_exc.HTTPError as exc:
            self._logger.warning(self.dump_response(response, dump_body))
            response = exc.response
            if raise_on_exc or self._raise_on_exc:
                raise
        else:
            self._logger.info(self.dump_response(response, dump_body))

        if kwargs.get('stream') is True:
            body = response.iter_content(chunk_size, decode_unicode)
        elif 'json' in (response.headers.get('Content-Type') or ''):
            body = response.json()
        else:
            body = response.text

        return ObjectDict(
            body=body,
            status=response.status_code,
            headers=dict(response.headers)
        )

    def get(self, uri, **kwargs):
        return self.request(uri, **kwargs)

    def post(self, uri, **kwargs):
        return self.request(uri, method='POST', **kwargs)

    def put(self, uri, **kwargs):
        return self.request(uri, method='PUT', **kwargs)

    def patch(self, uri, **kwargs):
        return self.request(uri, method='PATCH', **kwargs)

    def delete(self, uri, **kwargs):
        return self.request(uri, method='DELETE', **kwargs)

    def options(self, uri, **kwargs):
        return self.request(uri, method='OPTIONS', **kwargs)

    def head(self, uri, **kwargs):
        return self.request(uri, method='HEAD', **kwargs)


class JsonRPCClient(HTTPClient):
    def __init__(self, endpoint, uri, version='2.0', **kwargs):
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
            method='POST',
            json=dict(
                jsonrpc=self._version,
                method=method,
                params=params or {},
                id=self._request_id
            ),
            **kwargs
        )

        return resp.body or ObjectDict()


class FlaskelHttp(HTTPClient, FlaskelHTTPDumper):
    def __init__(self, endpoint, **kwargs):
        kwargs.setdefault('logger', cap.logger)
        super().__init__(endpoint, **kwargs)
        self._timeout = cap.config.HTTP_TIMEOUT or self._timeout

    def request(self, uri, **kwargs):
        if flask.request.id:
            if not kwargs.get('headers'):
                kwargs['headers'] = {}
            kwargs['headers'][cap.config.REQUEST_ID_HEADER] = flask.request.id

        return super().request(uri, **kwargs)
