import flask

from flaskel import cap, httpcode
from flaskel.http.client import FlaskelHttp
from flaskel.utils.datastruct import ObjectDict
from .base import BaseView


class ProxyView(BaseView):
    def __init__(
        self,
        host=None,
        url=None,
        method=None,
        proxy_body=False,
        proxy_headers=False,
        proxy_params=False,
        options=None,
        **kwargs,
    ):
        """

        :param host:
        :param url:
        :param method:
        :param proxy_body:
        :param proxy_headers:
        :param proxy_params:
        :param options: callable that returns dict to pass to http client instance
                        It overrides kwargs
        """
        self._host = host
        self._method = method
        self._url = url
        self._proxy_body = proxy_body
        self._proxy_headers = proxy_headers
        self._proxy_params = proxy_params
        self._options = kwargs

        if callable(options):
            self._options = {**kwargs, **options()}  # pragma: no cover

    # noinspection PyMethodMayBeStatic
    def _filter_kwargs(self, data):
        return data or {}

    def dispatch_request(self, *_, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        opts = {**self._options, **self._filter_kwargs(kwargs)}
        response = self.proxy(self.service(), **opts)

        return flask.Response(
            flask.stream_with_context(response.body),
            headers=response.headers,
            status=response.status,
        )

    def proxy(self, data, **kwargs):
        client = FlaskelHttp(data.host or self.upstream_host(), **kwargs)
        return client.request(
            data.url or self.request_url(),
            method=data.method or self.request_method(),
            headers=data.headers or self.request_headers(),
            params=data.params or self.request_params(),
            data=data.body or self.request_body(),
            stream=True,
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
            data=self.request_body(),
        )

    def upstream_host(self):
        return self._host

    def request_url(self):
        return self._url or flask.request.path

    def request_method(self):
        return self._method or flask.request.method

    def request_body(self):
        return flask.request.get_data() if self._proxy_body else None

    def request_headers(self):
        return flask.request.headers if self._proxy_headers else None

    def request_params(self):
        return flask.request.args if self._proxy_params else None


class ConfProxyView(BaseView):
    sep = "."
    config_key = None

    def __init__(self, config_key=None):
        self._config_key = config_key or config_key
        assert self._config_key is not None, "missing 'config_key'"

    def dispatch_request(self, *args, **kwargs):
        return self.perform(*args, **kwargs)

    def perform(self, *_, item=None, **__):
        """

        :param item:
        :return: ObjectDict
        """
        conf = cap.config
        keys = self._config_key.split(self.sep)
        if item is not None:
            keys += item.split(self.sep)
        for k in keys:
            conf = conf.get(k) or ObjectDict()
        if not conf:
            cap.logger.warning(f"unable to find conf keys: {self.sep.join(keys)}")
            flask.abort(httpcode.NOT_FOUND)
        return ObjectDict(**conf)


class TransparentProxyView(ProxyView):
    def __init__(self, **kwargs):
        kwargs.setdefault("proxy_body", True)
        kwargs.setdefault("proxy_headers", True)
        kwargs.setdefault("proxy_params", True)
        super().__init__(**kwargs)


class SchemaProxyView(ConfProxyView):
    default_urls = ["/schema/<path:filepath>"]

    def __init__(
        self,
        config_key="SCHEMAS",
        case_sensitive=False,
        ext_support=True,
        ext_name=".json",
    ):
        super().__init__(config_key)
        self.ext_name = ext_name
        self.ext_support = ext_support
        self.case_sensitive = case_sensitive

    def normalize(self, filepath):
        if self.ext_support and filepath.endswith(self.ext_name):
            filepath = self.sep.join(filepath.split(self.sep)[:-1])
        if self.case_sensitive is False:
            filepath = filepath.upper()

        return filepath.replace("/", self.sep)

    def dispatch_request(self, filepath, *args, **kwargs):
        schema_path = self.normalize(filepath)
        return super().perform(item=schema_path)
