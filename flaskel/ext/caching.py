import base64

from flask import request
from flask_caching import Cache as FlaskCache

from flaskel import httpcode, cap

caching = FlaskCache()


class Cache:
    cache = caching
    key_separator = "/"
    key_prefix = "/cached_request/"
    headers_in_keys = ("Content-Type",)
    cache_control_bypass = "no-store"
    default_timeout = None

    @classmethod
    def _optional_callable(cls, key):
        return key() if callable(key) else key

    @classmethod
    def unless(cls, *_, **__):
        bypass = cls._optional_callable(cls.cache_control_bypass)
        return bypass == request.headers.get("Cache-Control")

    @classmethod
    def response_filter(cls, response):
        try:
            if isinstance(response, (list, tuple)):
                return httpcode.is_ok(response[1])
            return httpcode.is_ok(response.status_code)
        except (IndexError, AttributeError) as exc:
            cap.logger.exception(exc)
            return None

    @classmethod
    def hash_method(cls, data: str):
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")

    @classmethod
    def _make_query_string(cls):
        query = sorted((pair for pair in request.args.items(multi=True)))
        return "&".join([f"{k}={v}" for k, v in query])

    @classmethod
    def make_cache_key(cls):
        key_prefix = cls._optional_callable(cls.key_prefix)
        separator = cls._optional_callable(cls.key_separator)
        cache_key = f"{request.root_url}{cls._make_query_string()}"

        for header in cls._optional_callable(cls.headers_in_keys):
            value = request.headers.get(header)
            if value:
                cache_key += f"{separator}{value}"

        hashed_key = cls.hash_method(cache_key)
        return f"{key_prefix}{separator}{hashed_key}"

    @classmethod
    def cached(cls, **kwargs):
        kwargs.setdefault("unless", cls.unless)
        kwargs.setdefault("timeout", cls.default_timeout)
        kwargs.setdefault("make_cache_key", cls.make_cache_key)
        kwargs.setdefault("response_filter", cls.response_filter)

        kwargs["timeout"] = cls._optional_callable(kwargs["timeout"])

        def decorator(f):
            @cls.cache.cached(**kwargs)
            def decorated_function(*args, **kw):
                return f(*args, **kw)

            return decorated_function

        return decorator
