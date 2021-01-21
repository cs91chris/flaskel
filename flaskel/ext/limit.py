import flask
from flask_ipban import IpBan
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


class FlaskIPBan:
    def __init__(self, app=None, ban=None):
        """

        :param app:
        :param ban: optional IpBan instance
        """
        self.ip_ban = ban

        if app:
            self.init_app(app)

    def init_app(self, app):
        count = app.config.IPBAN.count or 20
        seconds = app.config.IPBAN.seconds or 3600 * 24
        self.ip_ban = self.ip_ban or IpBan(ban_count=count, ban_seconds=seconds)
        self.ip_ban.init_app(app)


ip_ban = FlaskIPBan()
