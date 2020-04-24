import flask
from flask import current_app as cap
from requests import request as send_request, auth, exceptions as http_exc

from ..uuid import get_uuid
from . import http_status as httpcode


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
        r.headers['Authorization'] = "Bearer {}".format(self.token)
        return r


class HTTPClient:
    def __init__(self, endpoint, token=None, username=None, password=None, dump_body=False):
        """

        :param endpoint:
        :param token:
        :param username:
        :param password:
        :param dump_body:
        """
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._token = token
        self._dump_body = dump_body
        self._response = None

        if not self._endpoint.startswith('http'):
            self._endpoint = "http://{}".format(self._endpoint)

    def get_response_filename(self):
        """
        get filename from Content-Disposition header.
        i.e.: attachment; filename="<file name.ext>"

        :return: only the file name
        """
        hdr = self._response.headers.get('Content-Disposition')
        if not hdr:
            return None

        tmp = hdr.split(';')
        hdr = tmp[1] if len(tmp) > 1 else tmp[0]
        tmp = hdr.split('=')

        if len(tmp) > 1:
            return tmp[1].strip('"').lstrip('<').rstrip('>')
        else:
            return None

    @staticmethod
    def _dump_headers(hdr):
        """
        dumps http headers: useful for logging

        :param hdr: headers' dictionary
        :return: string representation of headers
                k1: v1
                k2: v2
        """
        return '\n'.join('{}: {}'.format(k, v) for k, v in hdr.items())

    def dump_request(self, dump_body=None):
        """
        dump http request: useful for logging

        :param dump_body: flag to enable or disable dump of request's body (overrides default)
        :return: prettified representation of input as string
        """
        req = self._response.request

        if dump_body is None:
            dump_body = self._dump_body

        if dump_body is True:
            req_body = req.body
        else:
            req_body = "request body not dumped"

        return 'REQUEST: {} {}\nheaders:\n{}\nbody:\n{}'.format(
            req.method, req.url, self._dump_headers(req.headers), req_body
        )

    def dump_response(self, dump_body=None):
        """
        dump http response: useful for logging

        :param dump_body: flag to enable or disable dump of response's body (overrides default)
        :return: prettified representation of input as string
        """
        resp = self._response
        hdr = resp.headers

        if dump_body is None:
            dump_body = self._dump_body

        if dump_body is True:
            resp_body = self.get_response_filename() or resp.text
        else:
            resp_body = "response body not dumped"

        return 'RESPONSE status code: {}\nheaders:\n{}\nbody:\n{}'.format(
            resp.status_code, self._dump_headers(hdr), resp_body
        )

    def request(self, uri, method='GET', raise_on_exc=False, dump_body=None, **kwargs):
        """

        :param method:
        :param uri:
        :param raise_on_exc:
        :param dump_body:
        :param kwargs:
        :return:
        """
        if self._username and self._password:
            kwargs['auth'] = auth.HTTPBasicAuth(self._username, self._password)

        if self._token:
            kwargs['auth'] = HTTPTokenAuth(self._token)

        try:
            url = "{}{}".format(self._endpoint, uri)
            self._response = send_request(method, url, **kwargs)
            cap.logger.info(self.dump_request())
        except (http_exc.ConnectionError, http_exc.Timeout) as exc:
            cap.logger.exception(exc)
            if raise_on_exc:
                flask.abort(httpcode.INTERNAL_SERVER_ERROR)
                return  # only to prevent warning

            return dict(body={}, status=httpcode.SERVICE_UNAVAILABLE, headers={})

        try:
            self._response.raise_for_status()
        except http_exc.HTTPError as exc:
            cap.logger.warning(self.dump_response(dump_body))
            self._response = exc.response
            if raise_on_exc:
                raise
        else:
            cap.logger.info(self.dump_response(dump_body))

        try:
            body = self._response.json()
        except ValueError as exc:
            cap.logger.debug(str(exc))
            body = dict(content=self._response.text)

        return dict(
            body=body,
            status=self._response.status_code,
            headers=self._response.headers
        )

    def get(self, uri, **kwargs):
        """

        :param uri:
        :param kwargs:
        :return:
        """
        return self.request(uri, 'GET', **kwargs)

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
        super().__init__(endpoint, **kwargs)
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
        kwargs.setdefault('raise_on_exc', True)
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

        return resp['body'] or {}
