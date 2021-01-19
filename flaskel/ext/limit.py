import flask
from flask_limiter import Limiter
from flaskel import cap
from flaskel.ext import cfremote
from flaskel import httpcode


def response_ok(r):
    return httpcode.is_ok(r.status_code)


def response_ko(r):
    return httpcode.is_ko(r.status_code)


limiter = Limiter(
    key_func=cfremote.get_remote,
    default_limits=[lambda: cap.config.LIMITER.FAIL],
    default_limits_deduct_when=response_ko
)


def header_whitelist():
    hdr = cap.config.LIMITER.BYPASS_KEY
    value = cap.config.LIMITER.BYPASS_VALUE
    return flask.request.headers.get(hdr) == value


@limiter.request_filter
def _header_whitelist():
    return header_whitelist()


limit_slow = limiter.limit(lambda: cap.config.LIMITER.SLOW, deduct_when=response_ok)
limit_medium = limiter.limit(lambda: cap.config.LIMITER.MEDIUM, deduct_when=response_ok)
limit_fast = limiter.limit(lambda: cap.config.LIMITER.FAST, deduct_when=response_ok)
limit_fail = limiter.limit(lambda: cap.config.LIMITER.FAIL, deduct_when=response_ko)
