import flask
from flask_limiter import Limiter

from flaskel import cap, httpcode
from flaskel.ext import cfremote


def response_ok(r):
    return httpcode.is_ok(r.status_code)


def response_ko(r):
    return r.status_code != httpcode.TOO_MANY_REQUESTS \
           and httpcode.is_ko(r.status_code)


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


class RateLimit:
    limiter = limiter

    @classmethod
    def slow(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.SLOW,
            deduct_when=response_ok
        )

    @classmethod
    def medium(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.MEDIUM,
            deduct_when=response_ok
        )

    @classmethod
    def fast(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.FAST,
            deduct_when=response_ok
        )

    @classmethod
    def fail(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.FAIL,
            deduct_when=response_ko
        )


limit_slow = RateLimit.slow()
limit_medium = RateLimit.medium()
limit_fast = RateLimit.fast()
limit_fail = RateLimit.fail()
