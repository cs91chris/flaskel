from requests import auth, exceptions as http_exc, request as send_request

from flaskel.utils.datastuct import ObjectDict
from flaskel.utils.faker import FakeLogger
from flaskel.utils.uuid import get_uuid
from . import http_status as httpcode
from .httpdumper import HTTPDumper


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
        return self.token == getattr(other, 'token', None)

    def __ne__(self, other):
        """

        :param other:
        :return:
        """
        return not self == other

    def __call__(self, r):
        """

        :param r:
        :return:
        """
        r.headers['Authorization'] = f"Bearer {self.token}"
        return r


class HTTPBase(HTTPDumper):
    def __init__(self, dump_body=False, raise_on_exc=False, logger=None):
        """

        :param dump_body:
        :param raise_on_exc:
        :param logger:
        """
        self._dump_body = dump_body
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
    def __init__(self, endpoint, token=None, username=None, password=None,
                 raise_on_exc=False, dump_body=False, logger=None):
        """

        :param endpoint:
        :param token:
        :param username:
        :param password:
        :param dump_body:
        :param raise_on_exc:
        :param logger:
        """
        super().__init__(dump_body, raise_on_exc, logger)
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

    def request(self, uri, method='GET',
                dump_body=None, chunk_size=None, decode_unicode=False, **kwargs):
        """

        :param method:
        :param uri:
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
            response = send_request(method, f"{self._endpoint}{uri}", **kwargs)
            self._logger.info(self.dump_request(response.request))
        except (http_exc.ConnectionError, http_exc.Timeout) as exc:
            self._logger.exception(exc)
            if self._raise_on_exc:
                raise

            return ObjectDict(dict(
                body={},
                status=httpcode.SERVICE_UNAVAILABLE,
                headers={},
                exception=exc
            ))

        try:
            response.raise_for_status()
        except http_exc.HTTPError as exc:
            self._logger.warning(self.dump_response(response, dump_body))
            response = exc.response
            if self._raise_on_exc:
                raise
        else:
            self._logger.info(self.dump_response(response, dump_body))

        if kwargs.get('stream') is True:
            body = response.iter_content(chunk_size, decode_unicode)
        elif 'json' in (response.headers.get('Content-Type') or ''):
            body = response.json()
        else:
            body = response.text

        return ObjectDict(dict(
            body=body,
            status=response.status_code,
            headers=dict(response.headers)
        ))

    def get(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, **kwargs)

    def post(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, 'POST', **kwargs)

    def put(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, 'PUT', **kwargs)

    def patch(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, 'PATCH', **kwargs)

    def delete(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, 'DELETE', **kwargs)


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
        if not method:
            raise ValueError('method must be a valid string')

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

        return ObjectDict(resp['body'] or {})
