from datetime import datetime

import flask
from flask import current_app as cap
from packaging import version

from flaskel import ExtProxy, Response
from flaskel.ext import builder, limit
from flaskel.http import httpcode
from flaskel.utils import webargs
from flaskel.views import BaseView


class RedisStore:
    def __init__(self, redis=None, sep='::'):
        self._sep = sep
        self._redis = redis

    def _normalize(self, ver):
        s = ver.decode().split(self._sep)
        return version.parse(s[0]), bool(int(s[1])) if len(s) > 1 else False

    def release(self, key, v, u=False):
        if self._redis.lpush(key, f'{v}{self._sep}{int(u)}'):
            return version.parse(v), u

    def latest(self, key):
        ver = self.retrieve(key)
        if len(ver):
            return ver[0]
        return None, None

    def pop(self, key):
        res = self._redis.lpop(key)
        return self._normalize(res)

    def clear(self, key):
        return self._redis.delete(key)

    def retrieve(self, key, max_item=1):
        data = self._redis.lrange(key, 0, max_item - 1)
        return [self._normalize(d) for d in data]


class MobileVersionCompatibility:
    def __init__(self, app=None, store=None, current_version=None):
        self._versions = []
        self._load_time = None
        self._store = store
        self._current_version = current_version

        if app is not None:
            self.init_app(app, store, current_version)  # pragma: no cover

    def init_app(self, app, store=None, current_version=None):
        self._store = store or self._store
        self._current_version = current_version or self._current_version
        if not self._current_version:
            self._current_version = getattr(app, 'version', None)

        self.load_config(app)
        self.load_from_storage()
        app.extensions['mobile_version'] = self

        @app.before_request
        def set_mobile_version():
            self._set_mobile_version()

        @app.after_request
        def set_version_headers(resp):
            return self._set_version_headers(resp)

    @property
    def mobile_version(self):
        return flask.g.get('mobile_version')

    @property
    def store(self):  # pragma: no cover
        return self._store

    @property
    def versions(self):
        return self._versions or self.load_from_storage()

    @staticmethod
    def load_config(app):
        app.config.setdefault('VERSION_STORE_MAX', 5)
        app.config.setdefault('VERSION_CACHE_EXPIRE', 60)
        app.config.setdefault('VERSION_API_HEADER', 'X-Api-Version')
        app.config.setdefault('VERSION_STORE_KEY', 'x_upgrade_needed')
        app.config.setdefault('VERSION_HEADER_KEY', 'X-Mobile-Version')
        app.config.setdefault('VERSION_UPGRADE_HEADER', 'X-Upgrade-Needed')
        app.config.setdefault('VERSION_SKIP_STATUSES', (
            httpcode.NOT_FOUND,
            httpcode.METHOD_NOT_ALLOWED,
            httpcode.FORBIDDEN,
            httpcode.TOO_MANY_REQUESTS,
        ))

    @staticmethod
    def version_parse(ver):
        return version.Version(ver)

    @staticmethod
    def _set_mobile_version():
        flask.g.mobile_version = flask.request.headers.get(cap.config.VERSION_HEADER_KEY)

    def _set_version_headers(self, resp):
        if resp.status_code not in cap.config.VERSION_SKIP_STATUSES:
            upgrade = self.check_upgrade()
            resp.headers[cap.config.VERSION_UPGRADE_HEADER] = int(upgrade)
            resp.headers[cap.config.VERSION_API_HEADER] = self._current_version
        return resp

    def latest(self):
        return str(self._versions[0][0]) if len(self._versions) > 0 else ''

    def all_releases(self):
        return [{'version': str(v), 'critical': u} for v, u in self._versions]

    def rollback(self):
        self._store.pop(cap.config.VERSION_STORE_KEY)
        self._versions = self._versions[1:]

    def clear(self):
        self._store.clear(cap.config.VERSION_STORE_KEY)
        self._versions = []

    def publish(self, ver, critical=False):
        key = cap.config.VERSION_STORE_KEY
        latest, _ = self._store.latest(key)
        if latest is not None and latest >= self.version_parse(ver):
            raise ValueError('New version must be greater than latest')

        self._store.release(cap.config.VERSION_STORE_KEY, ver, critical)
        return self.load_from_storage(force=True)

    def load_from_storage(self, force=False):
        if not force and self._load_time:
            seconds = (datetime.now() - self._load_time).seconds
            if seconds < cap.config.VERSION_CACHE_EXPIRE:
                return self._versions
        try:
            self._versions = self._store.retrieve(
                cap.config.VERSION_STORE_KEY, cap.config.VERSION_STORE_MAX
            )
            self._load_time = datetime.now()
        except Exception as exc:
            cap.logger.exception(exc)

        return self._versions

    def check_upgrade(self):
        if not self.mobile_version:
            return False

        self.load_from_storage()

        try:
            mv = self.version_parse(self.mobile_version)
            for v, u in self._versions:
                if v > mv and u is True:
                    return True
                if v <= mv:
                    return False
        except Exception as exc:
            cap.logger.exception(exc)
            return False

        return len(self._versions) >= cap.config.VERSION_STORE_MAX


class MobileReleaseView(BaseView):
    builder = builder
    ext = ExtProxy('mobile_version')
    methods = ['POST', 'GET', 'DELETE']
    default_view_name = 'mobile_release'
    default_urls = [
        '/mobile/release',
        '/mobile/release/<ver>',
    ]

    @webargs.query(dict(critical=webargs.OptField.boolean(), all=webargs.OptField.boolean()))
    def dispatch_request(self, params=None, ver=None, *args, **kwargs):
        if ver == 'latest':
            return self.ext.latest(), {'Content-Type': 'text/plain'}

        if ver is None:
            if flask.request.method == 'DELETE':
                if params['all']:
                    self.ext.clear()
                    return Response.no_content()
                self.ext.rollback()

            mimetype, response = self.builder.get_mimetype_accept()
            return response.build(self.ext.all_releases()), {'Content-Type': mimetype}

        try:
            self.ext.publish(ver, params['critical'])
        except ValueError as exc:
            flask.abort(httpcode.BAD_REQUEST, response=dict(reason=str(exc)))
        return Response.no_content()


class MobileLoggerView(BaseView):
    methods = ['POST']
    unavailable = "N/A"
    intro = "An exception occurred on mobile app:"
    default_view_name = 'mobile_logger'
    default_urls = (
        '/mobile/logger',
    )
    decorators = (
        builder.no_content,
        limit.RateLimit.medium(),
        limit.RateLimit.fail(),
    )

    def dump_log(self, data, key):
        return data.get(key) or self.unavailable

    def get_user_info(self, *args, **kwargs):
        return self.unavailable

    def dispatch_request(self, *args, **kwargs):
        payload = flask.request.json
        stacktrace = self.dump_log(payload, 'stacktrace').replace('\\n', '\n')
        cap.logger.error(
            f"{self.intro}"
            f"\n\tUser-Info: {self.get_user_info(*args, **kwargs)}"
            f"\n\tMobile-Version: {self.dump_log(flask.request.headers, 'X-Mobile-Version')}"
            f"\n\tUser-Agent: {self.dump_log(flask.request.headers, 'User-Agent')}"
            f"\n\tDevice-Info: {self.dump_log(payload, 'device_info')}"
            f"\n\tDebug-Info: {self.dump_log(payload, 'debug_info')}"
            f"\n\tPayload: {self.dump_log(payload, 'payload')}"
            f"\n\tStack-Trace:\n{stacktrace}"
        )
        if 'debug' in flask.request.args:
            return payload, httpcode.SUCCESS


mobile_version = MobileVersionCompatibility()
