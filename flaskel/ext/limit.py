from flask_limiter import Limiter
from vbcore.http import httpcode

import flaskel

from .default import cfremote

cap = flaskel.cap
config = flaskel.ConfigProxy("LIMITER")


def response_ok(res) -> bool:
    return httpcode.is_ok(res.status_code)


def response_ko(res) -> bool:
    return res.status_code != httpcode.TOO_MANY_REQUESTS and httpcode.is_ko(
        res.status_code
    )


limiter: Limiter = Limiter(
    key_func=cfremote.get_remote,
    default_limits=[lambda: config["FAIL"]],
    default_limits_deduct_when=response_ko,
)


def header_whitelist() -> bool:
    if not config.BYPASS_VALUE:
        return False
    return flaskel.request.headers.get(config.BYPASS_KEY) == config.BYPASS_VALUE


@limiter.request_filter
def _header_whitelist():
    return header_whitelist()


class RateLimit:
    limiter: Limiter = limiter

    @classmethod
    def slow(cls):
        return cls.limiter.limit(lambda: config.SLOW, deduct_when=response_ok)

    @classmethod
    def medium(cls):
        return cls.limiter.limit(lambda: config.MEDIUM, deduct_when=response_ok)

    @classmethod
    def fast(cls):
        return cls.limiter.limit(lambda: config.FAST, deduct_when=response_ok)

    @classmethod
    def fail(cls):
        return cls.limiter.limit(lambda: config.FAIL, deduct_when=response_ko)
