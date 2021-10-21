import base64
import typing as t

import flask
from flask import request, current_app as cap
from flask_caching import Cache as FlaskCache

from flaskel.http import httpcode, HttpMethod

caching = FlaskCache()


class Cache:
    cache = caching
    default_timeout: t.Union[t.Callable, str] = None
    key_separator: t.Union[t.Callable, str] = "/"
    key_prefix: t.Union[t.Callable, str] = "/cached_request/"
    cache_control_bypass: t.Union[t.Callable, str] = "no-store"
    headers_in_keys: t.Union[t.Callable, t.Iterable[str]] = ("Content-Type",)
    cacheable_methods: t.Union[t.Callable, t.Iterable[str]] = (HttpMethod.GET,)

    @staticmethod
    def optional_callable(key):
        return key() if callable(key) else key

    @classmethod
    def unless(cls, *_, **__):
        if cap.config.get("CACHE_DISABLED"):
            return True

        bypass = cls.optional_callable(cls.cache_control_bypass)
        return bypass == request.headers.get("Cache-Control")

    @classmethod
    def response_filter(cls, response) -> bool:
        if flask.request.method not in cls.optional_callable(cls.cacheable_methods):
            return False
        if isinstance(response, flask.Response):
            return httpcode.is_ok(response.status_code)

        cap.logger.debug(
            "response is not of type Response, so no status code can be checked"
        )
        return False

    @classmethod
    def hash_method(cls, data: str):
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")

    @classmethod
    def _make_query_string(cls):
        query = sorted((pair for pair in request.args.items(multi=True)))
        return "&".join(f"{k}={v}" for k, v in query)

    @classmethod
    def make_cache_key(cls):
        key_prefix = cls.optional_callable(cls.key_prefix)
        separator = cls.optional_callable(cls.key_separator)
        cache_key = cls._make_query_string()

        for header in cls.optional_callable(cls.headers_in_keys):
            value = request.headers.get(header)
            if value:
                cache_key += f"{separator}{value}"

        hashed_key = cls.hash_method(cache_key)
        return f"{key_prefix}{separator}{request.base_url}{separator}{hashed_key}"

    @classmethod
    def cached(cls, **kwargs):
        def wrapper(f):
            def decorator(*args, **kw):
                kwargs.setdefault("unless", cls.unless)
                kwargs.setdefault("timeout", cls.default_timeout)
                kwargs.setdefault("make_cache_key", cls.make_cache_key)
                kwargs.setdefault("response_filter", cls.response_filter)

                kwargs["timeout"] = cls.optional_callable(kwargs["timeout"])

                @cls.cache.cached(**kwargs)
                def decorated_function():
                    return f(*args, **kw)

                return decorated_function()

            return decorator

        return wrapper
