from datetime import datetime

import flask
from flask import current_app as cap
from packaging import version

from flaskel import Response
from flaskel.ext import builder
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
            self.init_app(app, store, current_version)

    def init_app(self, app, store, current_version):
        self._store = store
        self._current_version = current_version

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
    def store(self):
        return self._store

    @property
    def versions(self):
        return self._versions or self.load_from_storage()

    @staticmethod
    def load_config(app):
        app.config.setdefault('VERSION_CACHE_EXPIRE', 60)
        app.config.setdefault('VERSION_STORE_MAX', 5)
        app.config.setdefault('VERSION_STORE_KEY', 'x_upgrade_needed')
        app.config.setdefault('VERSION_HEADER_KEY', 'X-Mobile-Version')
        app.config.setdefault('VERSION_UPGRADE_HEADER', 'X-Upgrade-Needed')
        app.config.setdefault('VERSION_API_HEADER', 'X-Api-Version')

    @staticmethod
    def _set_mobile_version():
        flask.g.mobile_version = flask.request.headers.get(cap.config.VERSION_HEADER_KEY)

    def _set_version_headers(self, resp):
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
        if latest is not None and latest >= version.parse(ver):
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
            mobile_version = version.parse(self.mobile_version)
            for v, u in self._versions:
                if v > mobile_version and u is True:
                    return True
                if v <= mobile_version:
                    return False
        except Exception as exc:
            cap.logger.exception(exc)
            return False

        return len(self._versions) >= cap.config.VERSION_STORE_MAX


class MobileRelease(BaseView):
    methods = ['POST', 'GET', 'DELETE']

    @webargs.query(dict(critical=webargs.OptField.boolean(), all=webargs.OptField.boolean()))
    def dispatch_request(self, params=None, ver=None, *args, **kwargs):
        ext = flask.current_app.extensions['mobile_version']

        if ver == 'latest':
            return ext.latest(), {'Content-Type': 'text/plain'}

        if ver is None:
            if flask.request.method == 'DELETE':
                if params['all']:
                    ext.clear()
                    return Response.no_content()
                ext.rollback()

            mimetype, response = builder.get_mimetype_accept()
            return response.build(ext.all_releases()), {'Content-Type': mimetype}

        try:
            ext.publish(ver, params['critical'])
        except ValueError as exc:
            flask.abort(httpcode.BAD_REQUEST, response=dict(reason=str(exc)))
        return Response.no_content()
