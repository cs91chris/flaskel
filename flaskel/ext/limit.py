from datetime import datetime

import flask
from flask_ipban import IpBan as _IPBan
from flask_limiter import Limiter

from flaskel import cap, httpcode
from flaskel.ext import cfremote
from flaskel.utils.datetime import Day


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


class IPBan(_IPBan):
    def _after_request(self, response):
        """
        method to call after a request to allow recording all unwanted status codes

        :param response:
        :return:
        """
        statuses = (httpcode.NOT_FOUND, httpcode.METHOD_NOT_ALLOWED, httpcode.NOT_IMPLEMENTED)
        if response.status_code in statuses:
            self.add()

        return response

    def _before_request_check(self):
        self.ip_record.update_from_other_instances()
        if self._is_excluded():
            return

        ip = self.get_ip()
        entry = self._ip_ban_list.get(ip)
        url = flask.request.environ.full_path

        if entry and entry.get('count', 0) > self.ban_count:
            if entry.get('permanent', False):
                flask.abort(httpcode.GONE)

            now = datetime.now()
            delta = now - entry.get('timestamp', now)
            if delta.seconds < self.ban_seconds or self.ban_seconds == 0:
                self._logger.info(f"IP: {ip} updated in ban list, at url: {url}")
                entry['count'] += 1
                entry['timestamp'] = now
                self.ip_record.write(ip, count=entry['count'])
                flask.abort(httpcode.GONE)

            entry['count'] = 0
            self._logger.debug(f"IP: {ip} expired from ban list, at url: {url}")

    def load_nuisances(self, conf=None):
        """
        load a yaml file of nuisance urls or ips that are commonly used by vulnerability scanners
        any access to one of these that produces unwanted status codes will ban the source ip.
        Each call to load_nuisances will add to the current list of nuisances

        :param conf:
        :return: the number of nuisances added from this file
        """
        count = 0
        for match_type in ['ip', 'string', 'regex']:
            values = conf.get(match_type) or ()
            for v in values:
                try:
                    self.url_block_pattern_add(v, match_type)
                    count += 1
                except Exception as e:
                    self._logger.exception(f"Exception {e} adding pattern {v}")

        return count


class FlaskIPBan:
    def __init__(self, app=None, ban=None, **kwargs):
        """

        :param app:
        :param ban: optional IpBan instance
        """
        self.ip_ban = ban or IPBan()

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, white_list=None, nuisances=None):
        """

        :param app:
        :param white_list:
        :param nuisances:
        """
        app.config.setdefault('IPBAN_COUNT', 20)
        app.config.setdefault('IPBAN_SECONDS', Day.seconds)
        self.ip_ban.ban_count = app.config.IPBAN_COUNT
        self.ip_ban.ban_seconds = app.config.IPBAN_SECONDS

        self.ip_ban.init_app(app)
        self.ip_ban.ip_whitelist_add(white_list or [])
        self.ip_ban.load_nuisances(conf=cap.config.IPBAN_NUISANCES or nuisances or {})
