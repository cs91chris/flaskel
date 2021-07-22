import logging
from datetime import datetime

import flask
from flask import current_app as cap
from packaging import version

from flaskel import ExtProxy
from flaskel import Response
from flaskel.ext import builder
from flaskel.ext import limit
from flaskel.http import httpcode
from flaskel.utils import webargs
from flaskel.views import BaseView


class RedisStore:
    def __init__(self, redis=None, sep="::"):
        self.sep = sep
        self.client = redis

    def _normalize(self, ver):
        s = ver.split(self.sep)
        return version.parse(s[0]), bool(int(s[1])) if len(s) > 1 else False

    def release(self, key, v, u=False):
        if self.client.lpush(key, f"{v}{self.sep}{int(u)}"):
            return version.parse(v), u
        return None

    def latest(self, key):
        ver = self.retrieve(key)
        if len(ver):
            return ver[0]
        return None, None

    def pop(self, key):
        res = self.client.lpop(key)
        return self._normalize(res) if res else None

    def clear(self, key):
        return self.client.delete(key)

    def retrieve(self, key, max_item=1):
        data = self.client.lrange(key, 0, max_item - 1)
        return [self._normalize(d) for d in data]


class MobileVersionCompatibility:
    def __init__(self, app=None, store=None, current_version=None):
        self._store = store
        self._load_time = None
        self._versions = {None: []}
        self._current_version = current_version

        if app is not None:
            self.init_app(app, store, current_version)  # pragma: no cover

    def init_app(self, app, store=None, current_version=None):
        self._store = store or self._store
        self._current_version = current_version or self._current_version
        if not self._current_version:
            self._current_version = getattr(app, "version", None)

        self.load_config(app)

        if app.config.VERSION_CHECK_ENABLED:
            try:
                self.load_from_storage()
            except Exception as exc:  # pragma: no cover pylint: disable=W0703
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
    def store(self):  # pragma: no cover
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
    def version_parse(ver):
        return version.Version(ver)

    @staticmethod
    def _set_mobile_version():
        # pylint: disable=E0237
        flask.g.mobile_version = flask.request.headers.get(
            cap.config.VERSION_HEADER_KEY
        )

    @staticmethod
    def agent_identity():
        family = flask.g.user_agent.os.family
        return family.lower() if family else None

    def _get_agent(self):
        agent = flask.request.headers.get(cap.config.VERSION_AGENT_HEADER)
        if agent in cap.config.VERSION_AGENTS:
            return agent
        flask.g.user_agent.parse()
        return self.agent_identity()

    def _set_version_headers(self, resp):
        if resp.status_code not in cap.config.VERSION_SKIP_STATUSES:
            resp.headers[cap.config.VERSION_UPGRADE_HEADER] = int(self.check_upgrade())
            resp.headers[cap.config.VERSION_API_HEADER] = self._current_version
        return resp

    def _agent_key(self, agent):
        return f"{cap.config.VERSION_STORE_KEY}{self._store.sep}{agent}"

    def latest(self, agent):
        versions = self._versions.get(agent) or []
        return str(versions[0][0]) if len(versions) > 0 else ""

    def all_releases(self, agent):
        versions = self._versions.get(agent) or []
        return [{"version": str(v), "critical": u} for v, u in versions]

    def rollback(self, agent):
        self._store.pop(self._agent_key(agent))
        if agent in self._versions and len(self._versions[agent]):
            self._versions[agent] = self._versions[agent][1:]

    def clear(self, agent):
        self._store.clear(self._agent_key(agent))
        if agent in self._versions:
            self._versions[agent] = []

    def publish(self, agent, ver, critical=False):
        latest, _ = self._store.latest(self._agent_key(agent))
        if latest is not None and latest >= self.version_parse(ver):
            raise ValueError("New version must be greater than latest")

        self._store.release(self._agent_key(agent), ver, critical)
        self.load_from_storage(force=True)
        return self._versions[agent]

    def load_from_storage(self, force=False):
        if self._load_time:
            seconds = (datetime.now() - self._load_time).seconds
            if not force and seconds < cap.config.VERSION_CACHE_EXPIRE:
                return
        for a in cap.config.VERSION_AGENTS:
            smax = cap.config.VERSION_STORE_MAX
            self._versions[a] = self._store.retrieve(self._agent_key(a), smax)
        self._load_time = datetime.now()

    def check_upgrade(self):
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
        except Exception as exc:  # pragma: no cover pylint: disable=W0703
            cap.logger.exception(exc)
            return False
        return len(versions) >= cap.config.VERSION_STORE_MAX


class MobileReleaseView(BaseView):
    builder = builder
    ext = ExtProxy("mobile_version")
    methods = ["POST", "GET", "DELETE"]
    default_view_name = "mobile_release"
    default_urls = [
        "/mobile/release",
        "/mobile/release/<ver>",
    ]

    @webargs.query(
        dict(
            all=webargs.OptField.boolean(),
            critical=webargs.OptField.boolean(),
            agent=webargs.Field.string(required=True),
        )
    )
    def dispatch_request(self, params, *_, ver=None, **__):
        agent = params["agent"]
        if agent not in cap.config.VERSION_AGENTS:
            flask.abort(
                httpcode.BAD_REQUEST,
                response=dict(
                    reason="agent not compatible", agents=cap.config.VERSION_AGENTS
                ),
            )

        if ver == "latest":
            return self.ext.latest(agent) or "", {"Content-Type": "text/plain"}

        if ver is None:
            if flask.request.method == "DELETE":
                if params["all"]:
                    self.ext.clear(agent)
                    return Response.no_content()
                self.ext.rollback(agent)
        else:
            try:
                self.ext.publish(agent, ver, params["critical"])
            except ValueError as exc:
                flask.abort(httpcode.BAD_REQUEST, response=dict(reason=str(exc)))

        mimetype, response = self.builder.get_mimetype_accept()
        return response.build(self.ext.all_releases(agent)), {"Content-Type": mimetype}


class MobileLoggerView(BaseView):
    methods = ["POST"]
    unavailable = "N/A"
    intro = "An exception occurred on mobile app:"
    default_view_name = "mobile_logger"
    default_urls = ("/mobile/logger",)
    decorators = [
        builder.no_content,
        limit.RateLimit.medium(),
        limit.RateLimit.fail(),
    ]

    def __init__(self, logger_name=None):
        """

        :param logger_name:
        """
        if logger_name:
            self._log = logging.getLogger(logger_name)  # pragma: no cover
        else:
            self._log = cap.logger

    def dump_key(self, data, key):
        return data.get(key) or self.unavailable

    def get_user_info(self, *_, **__):
        return self.unavailable

    def dump_message(self, payload, *args, **kwargs):
        return (
            "%s"
            "\n\tUser-Info: %s"
            "\n\tMobile-Version: %s"
            "\n\tUser-Agent: %s"
            "\n\tDevice-Info: %s"
            "\n\tDebug-Info: %s"
            "\n\tPayload: %s"
            "\n\tStack-Trace:\n%s",
            self.intro,
            self.get_user_info(*args, **kwargs),
            self.dump_key(flask.request.headers, "X-Mobile-Version"),
            self.dump_key(flask.request.headers, "User-Agent"),
            self.dump_key(payload, "device_info"),
            self.dump_key(payload, "debug_info"),
            self.dump_key(payload, "payload"),
            self.dump_key(payload, "stacktrace").replace("\\n", "\n"),
        )

    def perform(self, payload, *args, **kwargs):
        message, *args = self.dump_message(payload, *args, **kwargs)
        self._log.error(message, *args)
        return message, args

    def dispatch_request(self, *args, **kwargs):
        payload = flask.request.json
        self.perform(payload, *args, **kwargs)

        if "debug" in flask.request.args:
            return payload, httpcode.SUCCESS
        return None


mobile_version = MobileVersionCompatibility()
