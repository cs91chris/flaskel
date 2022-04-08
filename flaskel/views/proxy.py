import typing as t

from flask import stream_with_context
from vbcore import uuid
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod
from vbcore.http.client import HTTPBase
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.http.rpc import rpc_error_to_httpcode

from flaskel import abort, cap, flaskel, request
from flaskel.http.client import FlaskelHttp, FlaskelJsonRPC

from .base import BaseView


class ProxyView(BaseView):
    client_class: t.Type[HTTPBase] = FlaskelHttp

    def __init__(
        self,
        host: t.Optional[str] = None,
        url: t.Optional[str] = None,
        method: t.Optional[str] = None,
        proxy_body: bool = False,
        proxy_headers: bool = False,
        proxy_params: bool = False,
        stream: bool = True,
        skip_args: t.Tuple[str, ...] = (),
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
                    stream_with_context(response.body),
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

    def service(self) -> ObjectDict:
        return ObjectDict(
            host=self.upstream_host(),
            uri=self.request_url(),
            method=self.request_method(),
            headers=self.request_headers(),
            params=self.request_params(),
            data=self.request_body(),
        )

    def upstream_host(self) -> str:
        return self._host

    def request_url(self) -> str:
        return self._url or request.path

    def request_method(self) -> str:
        return self._method or request.method

    def request_body(self):
        return request.get_data() if self._proxy_body else None

    def request_headers(self) -> t.Optional[t.Dict[str, t.Any]]:
        return dict(request.headers.items()) if self._proxy_headers else None

    def request_params(self) -> t.Optional[t.Dict[str, t.Any]]:
        return request.args if self._proxy_params else None


class ConfProxyView(BaseView):
    sep = "."
    config_key = None

    def __init__(self, config_key: t.Optional[str] = None):
        self._config_key = config_key or self.config_key
        assert self._config_key is not None, "missing 'config_key'"

    def dispatch_request(self, *args, **kwargs):
        return self.perform(*args, **kwargs)

    def perform(self, *_, item=None, **__) -> ObjectDict:
        conf = cap.config
        keys = self._config_key.split(self.sep)
        if item is not None:
            keys += item.split(self.sep)
        for k in keys:
            conf = conf.get(k) or ObjectDict()
        if not conf:
            cap.logger.warning(f"unable to find conf keys: {self.sep.join(keys)}")
            abort(httpcode.NOT_FOUND)
        return conf


class TransparentProxyView(ProxyView):
    methods = [
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.GET,
        HttpMethod.DELETE,
    ]

    def __init__(
        self,
        host: t.Optional[str] = None,
        url: t.Optional[str] = None,
        method: t.Optional[str] = None,
        proxy_body: bool = True,
        proxy_headers: bool = True,
        proxy_params: bool = True,
        stream: bool = True,
        skip_args: t.Tuple[str, ...] = (),
        options: t.Optional[t.Callable] = None,
        **kwargs,
    ):
        super().__init__(
            host=host,
            url=url,
            method=method,
            proxy_body=proxy_body,
            proxy_headers=proxy_headers,
            proxy_params=proxy_params,
            skip_args=skip_args,
            stream=stream,
            options=options,
            **kwargs,
        )


class SchemaProxyView(ConfProxyView):
    default_view_name = "schema_proxy"
    default_urls = ("/schema/<path:filepath>",)

    def __init__(
        self,
        config_key: str = "SCHEMAS",
        case_sensitive: bool = False,
        ext_support: bool = True,
        ext_name: str = ".json",
    ):
        super().__init__(config_key)
        self.ext_name = ext_name
        self.ext_support = ext_support
        self.case_sensitive = case_sensitive

    def normalize(self, filepath: str) -> str:
        if self.ext_support and filepath.endswith(self.ext_name):
            filepath = self.sep.join(filepath.split(self.sep)[:-1])
        if self.case_sensitive is False:
            filepath = filepath.upper()

        return filepath.replace("/", self.sep)

    def dispatch_request(self, filepath, *args, **kwargs):
        schema_path = self.normalize(filepath)
        return super().perform(item=schema_path)


class JsonRPCProxy(ProxyView):
    default_view_name: str = "jsonrpc_proxy"
    response_content_type: str = ContentTypeEnum.JSON
    client_class: t.Type[FlaskelJsonRPC] = FlaskelJsonRPC

    methods = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    def __init__(
        self,
        url: t.Optional[str] = None,
        proxy_headers: bool = False,
        stream: bool = False,
        skip_args: t.Tuple[str, ...] = (),
        options: t.Optional[t.Callable] = None,
        namespace: t.Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            url=url,
            stream=stream,
            proxy_headers=proxy_headers,
            skip_args=skip_args,
            options=options,
            **kwargs,
        )
        self.namespace = namespace

    def proxy(self, data: ObjectDict, **kwargs) -> ObjectDict:
        url = self.request_url()
        client = self.client_class(url, url, **kwargs)

        if request.method == HttpMethod.GET:
            resp = client.request(
                self.request_method(),
                request_id=request.id or uuid.get_uuid(),
                stream=self._stream,
                params=self.request_params(),
                headers=self.request_headers(),
            )
            return self.prepare_response(resp)

        client.notification(
            self.request_method(),
            stream=self._stream,
            params=self.request_params(),
            headers=self.request_headers(),
        )
        return self.prepare_response()

    def prepare_response(
        self, resp: t.Optional[ObjectDict] = None, **kwargs
    ) -> ObjectDict:
        headers = {HeaderEnum.CONTENT_TYPE: self.response_content_type, **kwargs}
        status = httpcode.NO_CONTENT if resp is None else httpcode.SUCCESS

        if resp and resp.error is not None:
            status = rpc_error_to_httpcode(resp.error.code)
            abort(status, response=resp.error)

        return ObjectDict(body=resp, status=status, headers=headers)

    def request_url(self) -> str:
        return self._url

    def request_method(self) -> str:
        action = request.path.split("/")[-1]
        if self.namespace is None:
            return action
        return f"{self.namespace}.{action}"

    def request_params(self) -> dict:
        if request.method == HttpMethod.GET:
            return request.args.to_dict()
        return request.json
