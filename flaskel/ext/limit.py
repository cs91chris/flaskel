import re
import typing as t
from datetime import datetime

from flask_limiter import Limiter
from vbcore.datastruct import ObjectDict
from vbcore.date_helper import Day
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


class FlaskIPBan:
    DEFAULT_WHITELIST: t.Dict[str, ObjectDict] = {
        "^/.well-known/": ObjectDict(
            pattern=re.compile(r"^/.well-known"), match_type="regex"
        ),
        "/favicon.ico": ObjectDict(match_type="string"),
        "/robots.txt": ObjectDict(match_type="string"),
        "/ads.txt": ObjectDict(match_type="string"),
    }

    def __init__(self, app=None, **kwargs):
        self._ip_banned = {}
        self._url_blocked = {}
        self._ip_whitelist: t.Dict[str, bool] = {"127.0.0.1": True}
        self._url_whitelist: t.Dict[str, ObjectDict] = self.DEFAULT_WHITELIST

        if app:
            self.init_app(app, **kwargs)

    def init_app(
        self,
        app,
        whitelist: t.Optional[t.List[str]] = None,
        nuisances: t.Optional[dict] = None,
    ):
        app.config.setdefault("IPBAN_ENABLED", True)
        app.config.setdefault("IPBAN_COUNT", 20)
        app.config.setdefault("IPBAN_SECONDS", Day.seconds)
        app.config.setdefault("IPBAN_NUISANCES", nuisances or {})
        app.config.setdefault("IPBAN_STATUS_CODE", httpcode.FORBIDDEN)
        app.config.setdefault(
            "IPBAN_CHECK_CODES",
            (
                httpcode.NOT_FOUND,
                httpcode.METHOD_NOT_ALLOWED,
                httpcode.NOT_IMPLEMENTED,
            ),
        )

        if app.config.IPBAN_ENABLED is True:
            app.after_request(self.after_request_hook)
            app.before_request(self.before_request_hook)

            self.add_whitelist(whitelist)
            self.load_nuisances(conf=app.config.IPBAN_NUISANCES)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["ipban"] = self

    @staticmethod
    def get_ip() -> str:
        return flaskel.request.remote_addr

    @staticmethod
    def get_url() -> str:
        return flaskel.request.path

    def is_whitelisted(
        self, ip: t.Optional[str] = None, url: t.Optional[str] = None
    ) -> bool:
        """
        return true if this ip or url should not be checked
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

    def is_blocked(self, url: str = "", ip: t.Optional[str] = None) -> bool:
        """
        return true if the url or ip pattern matches an existing block

        :param url: (optional) the url to check
        :param ip: (optional) an ip to check
        :return:
        """
        for pattern, item in self._url_blocked.items():
            if item.match_type == "regex" and item.pattern.match(url):
                cap.logger.warning("url %s matches block pattern %s", url, pattern)
                return True
            if item.match_type == "string" and pattern == url:
                cap.logger.warning("url %s matches block string %s", url, pattern)
                return True
            if ip and item.match_type == "ip" and pattern == ip:
                cap.logger.warning("ip %s blocked by pattern %s", ip, pattern)
                return True

        return False

    def after_request_hook(self, response):
        """
        method to call after a request to allow recording all unwanted status codes
        """
        if response.status_code in cap.config.IPBAN_CHECK_CODES:
            self.ban_ip()

        return response

    def before_request_hook(self):
        if self.is_whitelisted():
            return

        ip = self.get_ip()
        url = self.get_url()
        entry = self._ip_banned.get(ip)

        if entry and (entry.count or 0) > cap.config.IPBAN_COUNT:
            if entry.permanent:
                flaskel.abort(cap.config.IPBAN_STATUS_CODE)

            now = datetime.now()
            delta = now - (entry.timestamp or now)
            if (
                delta.seconds < cap.config.IPBAN_SECONDS
                or cap.config.IPBAN_SECONDS == 0
            ):
                cap.logger.info("IP: %s updated in ban list, at url: %s", ip, url)
                entry.count += 1
                entry.timestamp = now
                flaskel.abort(cap.config.IPBAN_STATUS_CODE)

            entry.count = 0
            cap.logger.debug("IP: %s expired from ban list, at url: %s", ip, url)

    def add_url_block(self, url: str, match_type: str = "regex") -> int:
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

    def block_ip(
        self,
        ips: t.List[str],
        permanent: bool = False,
        timestamp=None,
        url: str = "block",
    ) -> int:
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

    def ban_ip(
        self, ip: t.Optional[str] = None, url: t.Optional[str] = None, timestamp=None
    ) -> bool:
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

        if self.is_whitelisted(ip=ip, url=url):
            return False

        entry = self._ip_banned.get(ip)
        # check url block list if no existing entry or existing entry has expired
        if (
            not entry
            or (entry and (entry.count or 0) < cap.config.IPBAN_COUNT)
            and self.is_blocked(url, ip=ip)
        ):
            self.block_ip([ip], url=url)
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

    def unban_ip(self, ip: str) -> bool:
        """
        remove from the ban list

        :param ip: ip to remove
        :return True if entry removed
        """
        if not self._ip_banned.get(ip):
            return False

        del self._ip_banned[ip]
        return True

    def load_nuisances(self, conf: t.Optional[dict] = None) -> int:
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
                self.add_url_block(v, match_type)
                count += 1

        return count

    def add_whitelist(self, ips: t.Union[str, t.List[str]]) -> int:
        """

        :param ips: list of ip addresses to add
        :return: number of entries in the ip whitelist
        """
        if not isinstance(ips, list):
            ips = [ips]

        for ip in ips:
            self._ip_whitelist[ip] = True

        return len(self._ip_whitelist)

    def remove_whitelist(self, ip: str) -> bool:
        if ip not in self._ip_whitelist:
            return False

        del self._ip_whitelist[ip]
        return True


ipban = FlaskIPBan()
