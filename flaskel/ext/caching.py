from functools import partial

from flask import request
from flask_caching import Cache as FlaskCache

from flaskel.http import httpcode

caching = FlaskCache()


class Cache:
    cache = caching

    cached = partial(
        cache.cached,
        unless=lambda: 'no-store' in (request.headers.get('Cache-Control') or ''),
        response_filter=lambda r: httpcode.is_ok(r.status_code)
    )
