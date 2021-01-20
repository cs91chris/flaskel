import flask

from flaskel import cap
from flaskel.http import FlaskelHttp
from flaskel.utils.datastruct import ObjectDict
from .base import BaseView


class ProxyView(BaseView):
    def __init__(self, host=None, url=None, method=None,
                 proxy_body=False, proxy_headers=False, proxy_params=False):
        """

        :param host:
        :param url:
        :param method:
        :param proxy_body:
        :param proxy_headers:
        :param proxy_params:
        """
        self._host = host
        self._method = method
        self._url = url
        self._proxy_body = proxy_body
        self._proxy_headers = proxy_headers
        self._proxy_params = proxy_params

    def dispatch_request(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        response = self.proxy(self.service())
        return flask.Response(
            flask.stream_with_context(response.body),
            headers=response.headers,
            status=response.status
        )

    def proxy(self, data):
        return FlaskelHttp(data.host or self.upstream_host()).request(
            data.url or self.request_url(),
            method=data.method or self.request_method(),
            headers=data.headers or self.request_headers(),
            params=data.params or self.request_params(),
            data=data.body or self.request_body(),
            stream=True
        )

    def service(self):
        """

        :return: ObjectDict
        """
        return ObjectDict(
            host=self.upstream_host(),
            uri=self.request_url(),
            method=self.request_method(),
            headers=self.request_headers(),
            params=self.request_params(),
            data=self.request_body()
        )

    def upstream_host(self):
        return self._host

    def request_url(self):
        return self._url or flask.request.path

    def request_method(self):
        return self._method or flask.request.method

    def request_body(self):
        if self._proxy_body:
            return flask.request.get_data()

    def request_headers(self):
        if self._proxy_headers:
            return flask.request.headers

    def request_params(self):
        if self._proxy_params:
            return flask.request.params


class ConfProxyView(ProxyView):
    def __init__(self, config_key, **kwargs):
        super().__init__(**kwargs)
        self._config_key = config_key

    def service(self):
        """

        :return: ObjectDict
        """
        conf = cap.config
        keys = self._config_key.split('.')
        for k in keys:
            conf = conf.get(k) or ObjectDict()

        return ObjectDict(**conf)


class TransparentProxyView(ProxyView):
    def __init__(self, **kwargs):
        kwargs.setdefault('proxy_body', True)
        kwargs.setdefault('proxy_headers', True)
        kwargs.setdefault('proxy_params', True)
        super().__init__(**kwargs)
