import typing as t

import flask

import flaskel
from flaskel import cap, httpcode, HttpMethod, ConfigProxy
from flaskel.http.client import FlaskelHttp, FlaskelJsonRPC, HTTPBase
from flaskel.utils import ObjectDict, uuid
from .base import BaseView

# pylint: disable=too-many-instance-attributes
from ..http.rpc import rpc_error_to_httpcode


class ProxyView(BaseView):
    client_class: t.Type[HTTPBase] = FlaskelHttp

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        host: str = None,
        url: str = None,
        method: str = None,
        proxy_body: bool = False,
        proxy_headers: bool = False,
        proxy_params: bool = False,
        skip_args: t.Tuple[str, ...] = (),
        stream: bool = True,
        options: t.Optional[t.Callable] = None,
        **kwargs,
    ):
        """

        :param host:
        :param url:
        :param method:
        :param proxy_body:
        :param proxy_headers:
        :param proxy_params:
        :param stream: if False streaming response are disabled
        :param skip_args: a tuple o arguments name to remove from kwargs
                         it is necessary because flask pass url params to dispatch_request
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
        self._skip_args = skip_args
        self._stream = stream

        if callable(options):
            self._options = {**kwargs, **options()}  # pragma: no cover

    def _filter_kwargs(self, data: dict) -> dict:
        for arg in self._skip_args:
            data.pop(arg, None)
        return data

    def dispatch_request(self, *_, **kwargs):
        opts = {**self._options, **self._filter_kwargs(kwargs)}
        response = self.proxy(self.service(), **opts)

        if response and response.body and response.status != httpcode.NO_CONTENT:
            if self._stream:
                return flaskel.Response(
                    flask.stream_with_context(response.body),
                    status=response.status,
                    headers=response.headers,
                )
            return response.body, response.status, response.headers
        return flaskel.Response.no_content()

    def proxy(self, data: ObjectDict, **kwargs) -> ObjectDict:
        client = self.client_class(data.host or self.upstream_host(), **kwargs)
        return client.request(
            data.url or self.request_url(),
            method=data.method or self.request_method(),
            headers=data.headers or self.request_headers(),
            params=data.params or self.request_params(),
            data=data.body or self.request_body(),
            stream=self._stream,
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
        return dict(flask.request.headers.items()) if self._proxy_headers else None

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
    methods = [
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.GET,
        HttpMethod.DELETE,
    ]

    def __init__(self, **kwargs):
        kwargs.setdefault("proxy_body", True)
        kwargs.setdefault("proxy_headers", True)
        kwargs.setdefault("proxy_params", True)
        super().__init__(**kwargs)


class SchemaProxyView(ConfProxyView):
    default_view_name = "schema_proxy"
    default_urls = ("/schema/<path:filepath>",)

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


class JsonRPCProxy(ProxyView):
    response_content_type: str = "application/json"
    request_id_header: t.Callable = ConfigProxy("REQUEST_ID_HEADER")
    client_class: t.Type[FlaskelJsonRPC] = FlaskelJsonRPC

    methods = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("stream", False)
        super().__init__(*args, **kwargs)

    def proxy(self, data: ObjectDict, **kwargs) -> ObjectDict:
        url = self.upstream_host()
        client = self.client_class(url, url, **kwargs)

        if flask.request.method == HttpMethod.GET:
            resp = client.request(
                self.request_method(),
                request_id=self.get_request_id(),
                params=self.request_params(),
                stream=self._stream,
                headers=self.request_headers(),
            )
            return self.prepare_response(resp)

        client.notification(
            self.request_method(),
            params=self.request_params(),
            stream=self._stream,
            headers=self.request_headers(),
        )
        return self.prepare_response()

    def prepare_response(
        self, resp: t.Optional[ObjectDict] = None, **kwargs
    ) -> ObjectDict:
        headers = {"Content-Type": self.response_content_type, **kwargs}
        status = httpcode.NO_CONTENT if resp is None else httpcode.SUCCESS

        if resp and resp.error is not None:
            status = rpc_error_to_httpcode(resp.error.code)
            flask.abort(status, response=resp.error)

        return ObjectDict(body=resp, status=status, headers=headers)

    def get_request_id(self) -> str:
        header = self.request_id_header()
        return flask.request.headers.get(header) or uuid.get_uuid()

    def request_method(self) -> str:
        return flask.request.path.split("/")[-1]

    def request_params(self) -> dict:
        if flask.request.method == HttpMethod.GET:
            return flask.request.args.to_dict()
        return flask.request.json
