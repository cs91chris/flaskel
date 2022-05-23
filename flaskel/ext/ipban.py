import ipaddress
import typing as t
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import partial

from redis import Redis
from vbcore.datastruct import ExpiringCache, LRUCache
from vbcore.date_helper import Day
from vbcore.http import httpcode

from flaskel import abort, client_redis, flaskel

cap = flaskel.cap

IpType = t.Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
NetType = t.Union[ipaddress.IPv4Network, ipaddress.IPv6Network]


class IBanRepo(ABC):
    def __init__(self, *_, key_prefix: str = "", separator: str = "/", **__):
        self.separator = separator
        self.key_prefix = key_prefix

    def prepare_key(self, key: str) -> str:
        return f"{self.key_prefix}{self.separator}{key}"

    @abstractmethod
    def attempts(self, key: str) -> int:
        pass  # pragma: no cover

    @abstractmethod
    def ban(self, key: str, ttl: t.Optional[int] = None) -> int:
        pass  # pragma: no cover

    @abstractmethod
    def unban(self, key: str):
        pass  # pragma: no cover


class BanRepoRedis(IBanRepo):
    def __init__(self, client: Redis, **kwargs):
        super().__init__(**kwargs)
        self.client = client

    def attempts(self, key: str) -> int:
        value = self.client.get(self.prepare_key(key))
        return int(value) if value else 0

    def ban(self, key: str, ttl: t.Optional[int] = None) -> int:
        cache_key = self.prepare_key(key)
        pipe = self.client.pipeline()
        pipe.incr(cache_key)
        if ttl is not None:
            pipe.expire(cache_key, ttl)
        result = pipe.execute()
        return result[0]

    def unban(self, key: str):
        self.client.delete(self.prepare_key(key))


class BanRepoLocal(IBanRepo):
    def __init__(
        self,
        client_class: t.Type[LRUCache] = LRUCache,
        maxsize: int = 1000,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.client = client_class(maxsize)

    def get(self, key: str) -> t.Tuple[int, t.Optional[datetime]]:
        attempts, set_time = self.client.get(self.prepare_key(key)) or (0, None)
        if set_time and set_time < datetime.now():
            self.unban(key)
            return 0, None
        return attempts, set_time

    def attempts(self, key: str) -> int:
        return self.get(key)[0]

    def ban(self, key: str, ttl: t.Optional[int] = None) -> int:
        attempts, set_time = self.get(key)
        set_time = (
            None
            if ttl is None
            else (set_time or datetime.now()) + timedelta(seconds=ttl)
        )
        self.client.set(self.prepare_key(key), (attempts + 1, set_time))
        return attempts + 1

    def unban(self, key: str):
        try:
            del self.client[self.prepare_key(key)]
        except KeyError:
            pass


class IpBanService:
    def __init__(
        self,
        repo_class: t.Type[IBanRepo],
        key_prefix: str,
        max_attempts: t.Optional[int] = None,
        default_ttl: t.Optional[int] = None,
        **kwargs,
    ):
        self.default_ttl = default_ttl
        self.max_attempts = max_attempts
        self.white_list: t.Set[IpType] = set()
        self.net_white_list: t.Set[NetType] = set()
        self.ip: IBanRepo = repo_class(key_prefix=key_prefix, **kwargs)
        self.black_list: IBanRepo = repo_class(
            key_prefix=self.ip.prepare_key("blacklist"), **kwargs
        )

    def load_whitelist(self, ip: t.Iterable[str] = (), net: t.Iterable[str] = ()):
        self.white_list.update(ipaddress.ip_address(i) for i in ip)
        self.net_white_list.update(ipaddress.ip_network(n) for n in net)

    def is_whitelisted(self, ip: str) -> bool:
        ip_addr = ipaddress.ip_address(ip)
        if ip_addr in self.white_list:
            return True
        for net in self.net_white_list:
            if ip_addr in net:
                return True
        return False

    def is_blacklisted(self, ip: str) -> bool:
        return bool(self.black_list.attempts(ip))

    def add_blacklist(self, ip: str):
        self.black_list.ban(ip, ttl=None)  # never expires

    def ban(
        self, ip: str, ttl: t.Optional[int] = None, permanent: bool = False
    ) -> t.Optional[int]:
        if permanent is True:
            return self.black_list.ban(ip)

        if self.is_whitelisted(ip) or self.is_blacklisted(ip):
            return None
        return self.ip.ban(ip, ttl or self.default_ttl)

    def is_banned(self, ip: str) -> bool:
        if self.is_whitelisted(ip):
            return False
        if self.is_blacklisted(ip):
            return True

        return self.ip.attempts(ip) >= self.max_attempts


class FlaskIPBan:
    def __init__(self, app=None, **kwargs):
        self.service: t.Optional[IpBanService] = None
        self.backends: t.Dict[str, t.Type[IBanRepo]] = {}

        self.register_backend("local", BanRepoLocal, client_class=ExpiringCache)
        self.register_backend("redis", BanRepoRedis, client=client_redis)

        if app is not None:
            self.init_app(app, **kwargs)

    @classmethod
    def set_default_config(cls, app):
        app.config.setdefault("IPBAN_ENABLED", True)
        app.config.setdefault("IPBAN_KEY_PREFIX", app.config.APP_NAME)
        app.config.setdefault("IPBAN_KEY_SEP", "/")
        app.config.setdefault("IPBAN_BACKEND", "local")
        app.config.setdefault("IPBAN_BACKEND_OPTS", {})
        app.config.setdefault("IPBAN_COUNT", 20)
        app.config.setdefault("IPBAN_SECONDS", Day.seconds)
        app.config.setdefault("IPBAN_NET_WHITELIST", ["127.0.0.0/8"])
        app.config.setdefault("IPBAN_IP_WHITELIST", ["127.0.0.1"])
        app.config.setdefault("IPBAN_STATUS_CODE", httpcode.FORBIDDEN)
        app.config.setdefault(
            "IPBAN_CHECK_CODES",
            (
                httpcode.NOT_FOUND,
                httpcode.METHOD_NOT_ALLOWED,
                httpcode.NOT_IMPLEMENTED,
            ),
        )

    def init_app(self, app, service_class: t.Type[IpBanService] = IpBanService):
        self.set_default_config(app)
        if app.config.IPBAN_ENABLED is True:
            app.after_request(self.after_request_hook)
            app.before_request(self.before_request_hook)
            self.service = self.service_factory(service_class, app.config)
            self.service.load_whitelist(
                ip=app.config.IPBAN_IP_WHITELIST, net=app.config.IPBAN_NET_WHITELIST
            )

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["ipban"] = self

    def service_factory(self, service_class: t.Type[IpBanService], config):
        return service_class(
            self.backends[config.IPBAN_BACKEND],
            max_attempts=config.IPBAN_COUNT,
            default_ttl=config.IPBAN_SECONDS,
            key_prefix=config.IPBAN_KEY_PREFIX,
            separator=config.IPBAN_KEY_SEP,
            **config.IPBAN_BACKEND_OPTS,
        )

    def register_backend(
        self, name: str, repo_class: t.Type[IBanRepo], *args, **kwargs
    ):
        backend = partial(repo_class, *args, **kwargs)
        self.backends[name] = t.cast(t.Type[IBanRepo], backend)

    @classmethod
    def get_ip(cls) -> str:
        return flaskel.request.remote_addr

    def after_request_hook(self, response):
        if response.status_code in cap.config.IPBAN_CHECK_CODES:
            ip = self.get_ip()
            attempts = self.service.ban(ip)
            if attempts:
                cap.logger.info("%s added to ban list with attempts: %s", ip, attempts)
        return response

    def before_request_hook(self):
        ip = self.get_ip()
        if self.service.is_banned(ip):
            cap.logger.warn("%s is banned", ip)
            abort(cap.config.IPBAN_STATUS_CODE)


ipban = FlaskIPBan()
