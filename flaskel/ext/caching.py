import functools
import typing as t
from base64 import b64encode

from flask_caching import Cache as FlaskCache
from vbcore.http import httpcode, HttpMethod
from vbcore.http.headers import HeaderEnum

from flaskel.flaskel import cap, request, Response


class Caching(FlaskCache):
    def __init__(
        self,
        app=None,
        with_jinja2_ext: bool = True,
        config: t.Optional[dict] = None,
        key_separator: t.Union[t.Callable, str] = "/",
        key_prefix: t.Union[t.Callable, str] = "/cached_request",
        default_timeout: t.Union[t.Callable, str] = None,
        cache_control_bypass: t.Union[t.Callable, str] = "no-store",
        headers_in_keys: t.Union[t.Callable, t.Iterable[str]] = (
            HeaderEnum.CONTENT_TYPE,
        ),
        cacheable_methods: t.Union[t.Callable, t.Iterable[str]] = (HttpMethod.GET,),
    ):
        self.key_prefix = key_prefix
        self.key_separator = key_separator
        self.default_timeout = default_timeout
        self.headers_in_keys = headers_in_keys
        self.cacheable_methods = cacheable_methods
        self.cache_control_bypass = cache_control_bypass
        super().__init__(app, with_jinja2_ext, config)

    @staticmethod
    def optional_callable(key):
        return key() if callable(key) else key

    @staticmethod
    def hash_method(data: str) -> str:
        encoding = "utf-8"
        return b64encode(data.encode(encoding)).decode(encoding)

    @staticmethod
    def make_query_string() -> str:
        tokens: t.List[str] = []
        query = (pair for pair in request.args.items(multi=True))
        for param, value in query:
            tokens.extend(f"{param}={v}" for v in value)
        return "&".join(sorted(tokens))

    @staticmethod
    def make_headers_string(headers: t.List[str], separator: str) -> str:
        tokens: t.List[str] = []
        for header in headers:
            value = request.headers.get_all(header)
            tokens.extend(value[0].split(", ") if len(value) == 1 else value)
        return separator.join((sorted(tokens)))

    def unless(self, *_, **__) -> bool:
        if cap.config.CACHE_DISABLED:
            return True

        bypass = self.optional_callable(self.cache_control_bypass)
        return bypass == request.headers.get(HeaderEnum.CACHE_CONTROL)

    def response_filter(self, response) -> bool:
        if request.method not in self.optional_callable(self.cacheable_methods):
            return False
        if isinstance(response, Response):
            return httpcode.is_ok(response.status_code)

        cap.logger.debug(
            "response is not of type Response, so no status code can be checked"
        )
        return False

    def make_cache_key(self) -> str:
        """
        Returns a string formatted as follow:
            <prefix><sep><url><sep>[<query><sep><headers>]

        string between [] is hashed with ``hash_method``
        note that query string and headers are sorted
        """
        key_prefix = self.optional_callable(self.key_prefix)
        separator = self.optional_callable(self.key_separator)
        url = request.base_url.rstrip(separator)
        query = self.make_query_string()
        headers = self.optional_callable(self.headers_in_keys)
        headers = self.make_headers_string(headers, separator)
        hashed_key = self.hash_method(f"{query}{separator}{headers}")
        return f"{key_prefix}{separator}{url}{separator}{hashed_key}"

    def superclass_cached(self, **kwargs):
        """This is here only to mock it in tests, until a better way is found"""
        return super().cached(**kwargs)

    def cached(self, **kwargs):
        def wrapper(f):
            @functools.wraps(f)
            def decorator(*args, **kw):
                kwargs.setdefault("unless", self.unless)
                kwargs.setdefault("timeout", self.default_timeout)
                kwargs.setdefault("make_cache_key", self.make_cache_key)
                kwargs.setdefault("response_filter", self.response_filter)
                kwargs["timeout"] = self.optional_callable(kwargs["timeout"])
                return self.superclass_cached(**kwargs)(f, *args, **kw)

            return decorator

        return wrapper
