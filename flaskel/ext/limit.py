from datetime import datetime

import flask
from flask_ipban import IpBan as _IPBan
from flask_limiter import Limiter

from flaskel import cap, httpcode, yaml
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

    def get_ip(self):
        if self.ip_header:
            return flask.request.headers.get(self.ip_header)
        return cfremote.get_remote()

    def _before_request_check(self):
        self.ip_record.update_from_other_instances()
        if self._is_excluded():
            return

        ip = self.get_ip()
        entry = self._ip_ban_list.get(ip)
        url = flask.request.environ.get('PATH_INFO')

        if entry and entry.get('count', 0) > self.ban_count:
            now = datetime.now()
            delta = now - entry.get('timestamp', now)

            if entry.get('permanent', False):
                flask.abort(httpcode.GONE)

            if delta.seconds < self.ban_seconds or self.ban_seconds == 0:
                self._logger.info(f"IP: {ip} updated in ban list, at url: {url}")
                entry['count'] += 1
                entry['timestamp'] = now
                self.ip_record.write(ip, count=entry['count'])
                flask.abort(httpcode.GONE)

            entry['count'] = 0
            self._logger.debug(f"IP: {ip} expired from ban list, at url: {url}")

    def load_nuisances(self, file_name=None, conf=None):
        """
        load a yaml file of nuisance urls or ips that are commonly used by vulnerability scanners
        any access to one of these that produces unwanted status codes will ban the source ip.
        Each call to load_nuisances will add to the current list of nuisances

        :param file_name: a file name of your own nuisance ips
        :param conf:
        :return: the number of nuisances added from this file
        """
        added_count = 0

        if file_name:
            conf = yaml.load_yaml_file(file_name)

        for match_type in ['ip', 'string', 'regex']:
            for value in conf[match_type]:
                try:
                    self.url_block_pattern_add(value, match_type)
                    added_count += 1
                except Exception as e:
                    self._logger.exception(f"Exception {e} adding pattern {value}")

        return added_count


class FlaskIPBan:
    def __init__(self, app=None, ban=None, **kwargs):
        """

        :param app:
        :param ban: optional IpBan instance
        """
        self.ip_ban = ban

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, ban_count=20, ban_seconds=Day.seconds, white_list=None, **kwargs):
        """

        :param app:
        :param ban_count:
        :param ban_seconds:
        :param white_list:
        """
        count = app.config.IPBAN_COUNT or ban_count
        seconds = app.config.IPBAN_SECONDS or ban_seconds
        self.ip_ban = self.ip_ban or IPBan(ban_count=count, ban_seconds=seconds, **kwargs)
        self.ip_ban.init_app(app)
        self.ip_ban.ip_whitelist_add(white_list or [])
        self.ip_ban.load_nuisances(conf=cap.config.IPBAN_NUISANCES)


ip_ban = FlaskIPBan()
