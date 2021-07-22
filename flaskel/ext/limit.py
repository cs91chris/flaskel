import re
from datetime import datetime

import flask
from flask import current_app as cap
from flask_limiter import Limiter

from flaskel.ext.default import cfremote
from flaskel.http import httpcode
from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.datetime import Day


def response_ok(res):
    return httpcode.is_ok(res.status_code)


def response_ko(res):
    return res.status_code != httpcode.TOO_MANY_REQUESTS and httpcode.is_ko(
        res.status_code
    )


limiter = Limiter(
    key_func=cfremote.get_remote,
    default_limits=[lambda: cap.config["LIMITER"]["FAIL"]],
    default_limits_deduct_when=response_ko,
)


def header_whitelist():
    hdr = cap.config.LIMITER.BYPASS_KEY
    value = cap.config.LIMITER.BYPASS_VALUE
    return flask.request.headers.get(hdr) == value


@limiter.request_filter
def _header_whitelist():
    return header_whitelist()


class RateLimit:  # pragma: no cover
    limiter = limiter

    @classmethod
    def slow(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.SLOW, deduct_when=response_ok
        )

    @classmethod
    def medium(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.MEDIUM, deduct_when=response_ok
        )

    @classmethod
    def fast(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.FAST, deduct_when=response_ok
        )

    @classmethod
    def fail(cls):
        return cls.limiter.limit(
            lambda: cap.config.LIMITER.FAIL, deduct_when=response_ko
        )


class FlaskIPBan:
    def __init__(self, app=None, **kwargs):
        self._ip_banned = {}
        self._url_blocked = {}

        self._ip_whitelist = {"127.0.0.1": True}

        self._url_whitelist = {
            "^/.well-known/": ObjectDict(
                pattern=re.compile(r"^/.well-known"), match_type="regex"
            ),
            "/favicon.ico": ObjectDict(pattern=re.compile(""), match_type="string"),
            "/robots.txt": ObjectDict(pattern=re.compile(""), match_type="string"),
            "/ads.txt": ObjectDict(pattern=re.compile(""), match_type="string"),
        }

        if app:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(self, app, whitelist=(), nuisances=None):
        """

        :param app: flask app
        :param whitelist:
        :param nuisances:
        :return:
        """
        app.config.setdefault("IPBAN_ENABLED", True)
        app.config.setdefault("IPBAN_COUNT", 20)
        app.config.setdefault("IPBAN_SECONDS", Day.seconds)
        app.config.setdefault("IPBAN_NUISANCES", nuisances or {})
        app.config.setdefault("IPBAN_STATUS_CODE", httpcode.FORBIDDEN)
        app.config.setdefault(
            "IPBAN_CHECK_CODES",
            (httpcode.NOT_FOUND, httpcode.METHOD_NOT_ALLOWED, httpcode.NOT_IMPLEMENTED),
        )

        if app.config.IPBAN_ENABLED:
            app.after_request(self._after_request)
            app.before_request(self._before_request)

            self.add_whitelist(whitelist or [])
            self.load_nuisances(conf=cap.config.IPBAN_NUISANCES)

        if not hasattr(app, "extensions"):
            app.extensions = dict()  # pragma: no cover
        app.extensions["ipban"] = self

    @staticmethod
    def get_ip():
        return flask.request.remote_addr

    @staticmethod
    def get_url():
        return flask.request.path

    def _is_excluded(self, ip=None, url=None):
        """

        :return: true if this ip or url should not be checked
        """
        ip = ip or self.get_ip()
        url = url or self.get_url()

        for key, item in self._url_whitelist.items():
            if (item.match_type == "regex" and item.pattern.match(url)) or (
                item.match_type == "string" and key == url
            ):
                return True

        if ip in self._ip_whitelist:
            return True

        return False

    def _test_blocked(self, url="", ip=None):
        """
        return true if the url or ip pattern matches an existing block

        :param url: (optional) the url to check
        :param ip: (optional) an ip to check
        :return:
        """
        query_path = url.split("?")[0]
        for pattern, item in self._url_blocked.items():
            if item.match_type == "regex" and item.pattern.match(query_path):
                cap.logger.warning("url %s matches block pattern %s", url, pattern)
                return True
            if item.match_type == "string" and pattern == query_path:
                cap.logger.warning("url %s matches block string %s", url, pattern)
                return True
            if ip and item.match_type == "ip" and pattern == ip:
                cap.logger.warning("ip %s blocked by pattern %s", ip, pattern)
                return True

        return False

    def _after_request(self, response):
        """
        method to call after a request to allow recording all unwanted status codes

        :param response:
        :return:
        """
        if response.status_code in cap.config.IPBAN_CHECK_CODES:
            self.add()

        return response

    def _before_request(self):
        if self._is_excluded():
            return

        ip = self.get_ip()
        url = self.get_url()
        entry = self._ip_banned.get(ip)

        if entry and (entry.count or 0) > cap.config.IPBAN_COUNT:
            if entry.permanent:
                flask.abort(cap.config.IPBAN_STATUS_CODE)

            now = datetime.now()
            delta = now - (entry.timestamp or now)
            if (
                delta.seconds < cap.config.IPBAN_SECONDS
                or cap.config.IPBAN_SECONDS == 0
            ):
                cap.logger.info("IP: %s updated in ban list, at url: %s", ip, url)
                entry.count += 1
                entry.timestamp = now
                flask.abort(cap.config.IPBAN_STATUS_CODE)

            entry.count = 0
            cap.logger.debug("IP: %s expired from ban list, at url: %s", ip, url)

    def add_url_block(self, url, match_type="regex"):
        """
        add or replace the pattern to the list of url patterns to block

        :param match_type: regex or string - determines the match strategy to use
        :param url: regex pattern to match with requested url
        :return: length of the blocked list
        """
        self._url_blocked[url] = ObjectDict(
            pattern=re.compile(url), match_type=match_type
        )
        return len(self._url_blocked)

    def block(self, ips, permanent=False, timestamp=None, url="block"):
        """
        add a list of ip addresses to the block list

        :param ips: list of ip addresses to block
        :param permanent: (optional) True=do not allow entries to expire
        :param timestamp: use this timestamp instead of now()
        :param url: url or reason to block
        :returns number of entries in the block list
        """
        timestamp = timestamp or datetime.now()

        for ip in ips:
            entry = self._ip_banned.get(ip)
            if entry:
                entry.timestamp = timestamp
                entry.count = cap.config.IPBAN_COUNT * 2
                # retain permanent on extra blocks
                entry.permanent = entry.permanent or permanent
                cap.logger.warning("%s added to ban list", ip)
            else:
                self._ip_banned[ip] = ObjectDict(
                    timestamp=timestamp,
                    count=cap.config.IPBAN_COUNT * 2,
                    permanent=permanent,
                    url=url,
                )
                cap.logger.info("%s updated in ban list", ip)

        return len(self._ip_banned)

    def add(self, ip=None, url=None, timestamp=None):
        """
        increment ban count ip of the current request in the banned list

        :return:
        :param ip: optional ip to add (ip ban will by default use current ip)
        :param url: optional url to display/store
        :param timestamp: entry time to set
        :return True if entry added/updated
        """
        ip = ip or self.get_ip()
        url = url or self.get_url()

        if self._is_excluded(ip=ip, url=url):
            return False

        entry = self._ip_banned.get(ip)
        # check url block list if no existing entry or existing entry has expired
        if not entry or (entry and (entry.count or 0) < cap.config.IPBAN_COUNT):
            if self._test_blocked(url, ip=ip):
                self.block([ip], url=url)
                return True

        if not timestamp or (timestamp and timestamp > datetime.now()):
            timestamp = datetime.now()

        if entry:
            entry.timestamp = timestamp
            count = entry.count = entry.count + 1
        else:
            count = 1
            self._ip_banned[ip] = ObjectDict(timestamp=timestamp, count=count, url=url)

        cap.logger.info("%s %s added/updated ban list. Count: %d", ip, url, count)
        return True

    def remove(self, ip):
        """
        remove from the ban list

        :param ip: ip to remove
        :return True if entry removed
        """
        if not self._ip_banned.get(ip):
            return False

        del self._ip_banned[ip]
        return True

    def load_nuisances(self, conf=None):
        """
        load a yaml file of nuisance urls or ips that are commonly used by vulnerability scanners
        any access to one of these that produces unwanted status codes will ban the source ip.
        Each call to load_nuisances will add to the current list of nuisances

        :param conf:
        :return: the number of nuisances added from this file
        """
        count = 0
        for match_type in ["ip", "string", "regex"]:
            values = conf.get(match_type) or ()
            for v in values:
                try:
                    self.add_url_block(v, match_type)
                    count += 1
                except (ValueError, TypeError) as e:
                    cap.logger.error("an error occurred while adding pattern '%s'", v)
                    cap.logger.exception(e)

        return count

    def add_whitelist(self, ips):
        """

        :param ips: list of ip addresses to add
        :return: number of entries in the ip whitelist
        """
        if not isinstance(ips, (list, tuple)):
            ips = (ips,)

        for ip in ips:
            self._ip_whitelist[ip] = True

        return len(self._ip_whitelist)

    def remove_whitelist(self, el):
        if not self._ip_whitelist.get(el):
            return False

        del self._ip_whitelist[el]
        return True


ip_ban = FlaskIPBan()
