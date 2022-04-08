import logging
import typing as t
from datetime import datetime

import flask
from packaging import version
from vbcore.http import httpcode, HttpMethod
from vbcore.http.headers import ContentTypeEnum, HeaderEnum

from flaskel import abort, cap, ExtProxy, Flaskel, request, Response, webargs
from flaskel.ext.default import builder
from flaskel.ext.limit import RateLimit
from flaskel.views import BaseView


class RedisStore:
    def __init__(self, redis=None, sep: str = "/"):
        self.sep = sep
        self.client = redis

    @staticmethod
    def normalize_string(data) -> t.Optional[str]:
        if not data:
            return None
        return data if isinstance(data, str) else data.decode()

    def _normalize(self, ver: str):
        s = ver.split(self.sep)
        return version.parse(s[0]), bool(int(s[1])) if len(s) > 1 else False

    def release(self, key: str, v: str, u: bool = False):
        if self.client.lpush(key, f"{v}{self.sep}{int(u)}"):
            return version.parse(v), u
        return None

    def latest(self, key: str):
        ver = self.retrieve(key)
        if len(ver):
            return ver[0]
        return None, None

    def pop(self, key: str):
        res = self.normalize_string(self.client.lpop(key))
        return self._normalize(res) if res else None

    def clear(self, key: str):
        return self.client.delete(key)

    def retrieve(self, key: str, max_item: int = 1):
        data = self.client.lrange(key, 0, max_item - 1)
        return [self._normalize(self.normalize_string(d)) for d in data]


class MobileVersionCompatibility:
    def __init__(
        self, app: t.Optional[Flaskel] = None, store=None, current_version=None
    ):
        self._store = store
        self._load_time: t.Optional[datetime] = None
        self._current_version = current_version
        self._versions: t.Dict[t.Optional[str], list] = {None: []}

        if app is not None:
            self.init_app(app, store, current_version)

    def init_app(self, app: Flaskel, store=None, current_version=None):
        self._store = store or self._store
        self._current_version = current_version or self._current_version
        if not self._current_version:
            self._current_version = app.version

        self.load_config(app)

        if app.config.VERSION_CHECK_ENABLED:
            try:
                self.load_from_storage()
            except Exception as exc:  # pylint: disable=broad-except
                app.logger.exception(exc)

            app.before_request_funcs.setdefault(None, []).append(
                self._set_mobile_version
            )
            app.after_request_funcs.setdefault(None, []).append(
                self._set_version_headers
            )

        app.extensions["mobile_version"] = self

    @property
    def mobile_version(self):
        return flask.g.get("mobile_version")

    @property
    def store(self):
        return self._store

    @staticmethod
    def load_config(app):
        app.config.setdefault("VERSION_STORE_MAX", 6)
        app.config.setdefault("VERSION_CACHE_EXPIRE", 3600)
        app.config.setdefault("VERSION_CHECK_ENABLED", True)
        app.config.setdefault("VERSION_AGENT_HEADER", "X-Agent")
        app.config.setdefault("VERSION_API_HEADER", "X-Api-Version")
        app.config.setdefault("VERSION_STORE_KEY", "x_upgrade_needed")
        app.config.setdefault("VERSION_HEADER_KEY", "X-Mobile-Version")
        app.config.setdefault("VERSION_UPGRADE_HEADER", "X-Upgrade-Needed")
        app.config.setdefault("VERSION_AGENTS", ("android", "ios"))
        app.config.setdefault(
            "VERSION_SKIP_STATUSES",
            (
                httpcode.FORBIDDEN,
                httpcode.NOT_FOUND,
                httpcode.METHOD_NOT_ALLOWED,
                httpcode.TOO_MANY_REQUESTS,
            ),
        )

    @staticmethod
    def version_parse(ver: str) -> version.Version:
        return version.Version(ver)

    @staticmethod
    def _set_mobile_version():
        # pylint: disable=assigning-non-slot
        flask.g.mobile_version = request.headers.get(cap.config.VERSION_HEADER_KEY)

    @staticmethod
    def agent_identity() -> t.Optional[str]:
        family = flask.g.user_agent.os.family
        return family.lower() if family else None

    def _get_agent(self) -> t.Optional[str]:
        agent = request.headers.get(cap.config.VERSION_AGENT_HEADER)
        if agent in cap.config.VERSION_AGENTS:
            return agent
        flask.g.user_agent.parse()
        return self.agent_identity()

    def _set_version_headers(self, resp):
        if resp.status_code not in cap.config.VERSION_SKIP_STATUSES:
            resp.headers[cap.config.VERSION_UPGRADE_HEADER] = int(self.check_upgrade())
            resp.headers[cap.config.VERSION_API_HEADER] = self._current_version
        return resp

    def _agent_key(self, agent: str) -> str:
        return f"{cap.config.VERSION_STORE_KEY}{self._store.sep}{agent}"

    def latest(self, agent: str) -> str:
        versions = self._versions.get(agent) or []
        return str(versions[0][0]) if len(versions) > 0 else ""

    def all_releases(self, agent: str) -> t.List[t.Dict[str, t.Any]]:
        versions = self._versions.get(agent) or []
        return [{"version": str(v), "critical": u} for v, u in versions]

    def rollback(self, agent: str):
        self._store.pop(self._agent_key(agent))
        if agent in self._versions and len(self._versions[agent]):
            self._versions[agent] = self._versions[agent][1:]

    def clear(self, agent: str):
        self._store.clear(self._agent_key(agent))
        if agent in self._versions:
            self._versions[agent] = []

    def publish(self, agent: str, ver: str, critical: bool = False):
        latest, _ = self._store.latest(self._agent_key(agent))
        if latest is not None and latest >= self.version_parse(ver):
            raise ValueError("New version must be greater than latest")

        self._store.release(self._agent_key(agent), ver, critical)
        self.load_from_storage(force=True)
        return self._versions[agent]

    def load_from_storage(self, force: bool = False):
        if self._load_time:
            seconds = (datetime.now() - self._load_time).seconds
            if not force and seconds < cap.config.VERSION_CACHE_EXPIRE:
                return
        for a in cap.config.VERSION_AGENTS:
            smax = cap.config.VERSION_STORE_MAX
            self._versions[a] = self._store.retrieve(self._agent_key(a), smax)
        self._load_time = datetime.now()

    def check_upgrade(self) -> bool:
        if not self.mobile_version:
            return False
        try:
            self.load_from_storage()
            agent = self._get_agent()
            versions = self._versions.get(agent) or []
            mv = self.version_parse(self.mobile_version)
            for v, u in versions:
                if v > mv and u is True:
                    return True
                if v <= mv:
                    return False
        except Exception as exc:  # pylint: disable=broad-except
            cap.logger.exception(exc)
            return False
        return len(versions) >= cap.config.VERSION_STORE_MAX


class MobileReleaseView(BaseView):
    builder = builder
    ext: MobileVersionCompatibility = t.cast(
        MobileVersionCompatibility, ExtProxy("mobile_version")
    )
    methods = [
        HttpMethod.POST,
        HttpMethod.GET,
        HttpMethod.DELETE,
    ]

    default_view_name = "mobile_release"
    default_urls = (
        "/mobile/release",
        "/mobile/release/<ver>",
    )

    @webargs.query(
        dict(
            all=webargs.OptField.boolean(),
            critical=webargs.OptField.boolean(),
            agent=webargs.Field.string(required=True),
        )
    )
    def dispatch_request(self, params: dict, *_, ver=None, **__):
        agent = params["agent"]
        if agent not in cap.config.VERSION_AGENTS:
            return abort(
                httpcode.BAD_REQUEST,
                response=Response(
                    dict(
                        reason="agent not compatible", agents=cap.config.VERSION_AGENTS
                    )
                ),
            )

        if ver == "latest":
            return self.ext.latest(agent) or "", {
                HeaderEnum.CONTENT_TYPE: ContentTypeEnum.PLAIN
            }

        if ver is None:
            if request.method == "DELETE":
                if params["all"]:
                    self.ext.clear(agent)
                    return Response.no_content()
                self.ext.rollback(agent)
        else:
            try:
                self.ext.publish(agent, ver, params["critical"])
            except ValueError as exc:
                abort(httpcode.BAD_REQUEST, str(exc))

        mimetype, response = self.builder.get_mimetype_accept()
        return response.build(self.ext.all_releases(agent)), {
            HeaderEnum.CONTENT_TYPE: mimetype
        }


class MobileLoggerView(BaseView):
    unavailable = "N/A"
    intro = "An exception occurred on mobile app:"
    default_view_name = "mobile_logger"
    default_urls = ("/mobile/logger",)

    methods = [
        HttpMethod.POST,
    ]
    decorators = [
        builder.no_content,
        RateLimit.medium(),
        RateLimit.fail(),
    ]

    def __init__(self, name: t.Optional[str] = None):
        self._log = logging.getLogger(name) if name else cap.logger

    @staticmethod
    def _dump_dict(data: dict) -> str:
        return "\n\t".join(f"{k}: {v}" for k, v in data.items())

    def dump_key(self, data: dict, key: str) -> t.Optional[str]:
        if key not in data:
            return self.unavailable

        _data = data.get(key)
        if isinstance(_data, dict):
            return self._dump_dict(_data)
        return _data

    def get_user_info(self, *_, **__) -> str:
        return self.unavailable

    def dump_message(self, payload: dict, *args, **kwargs) -> t.Tuple[str, tuple]:
        return (
            (
                "%s"
                "\n\tUser-Info: %s"
                "\n\tMobile-Version: %s"
                "\n\tUser-Agent: %s"
                "\n\tDevice-Info: %s"
                "\n\tDebug-Info: %s"
                "\n\tPayload: %s"
                "\n\tStack-Trace:\n%s"
            ),
            (
                self.intro,
                self.get_user_info(*args, **kwargs),
                self.dump_key(request.headers, "X-Mobile-Version"),
                self.dump_key(request.headers, "User-Agent"),
                self.dump_key(payload, "device_info"),
                self.dump_key(payload, "debug_info"),
                self.dump_key(payload, "payload"),
                self.dump_key(payload, "stacktrace").replace("\\n", "\n"),
            ),
        )

    def perform(self, payload: dict, *args, **kwargs) -> t.Tuple[str, tuple]:
        message, args = self.dump_message(payload, *args, **kwargs)
        self._log.error(message, *args)
        return message, args

    def dispatch_request(self, *args, **kwargs):
        payload = request.json
        self.perform(payload, *args, **kwargs)

        if "debug" in request.args:
            return payload, httpcode.SUCCESS
        return None
