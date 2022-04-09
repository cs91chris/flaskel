import os
import sys
import typing as t

from flask import Blueprint
from flask.typing import AfterRequestCallable, BeforeRequestCallable
from jinja2 import ChoiceLoader, FileSystemLoader
from vbcore.db.events import register_engine_events
from vbcore.misc import random_string
from werkzeug.middleware.lint import LintMiddleware
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.routing import BaseConverter

from flaskel import config, flaskel

from .converters import CONVERTERS
from .flaskel import DumpUrls, Flaskel
from .middlewares import BaseMiddleware
from .views import BaseView

StrPathLikeType = t.Union[
    str,
    os.PathLike,
    t.Sequence[t.Union[str, os.PathLike]],
]
BlueprintType = t.Union[
    Blueprint,
    t.Tuple[Blueprint],
    t.Tuple[Blueprint, t.Dict[str, t.Any]],
]
WsgiCallable = t.Callable[[dict, t.Callable], t.Callable]
WsgiCallableType = t.TypeVar("WsgiCallableType", bound=WsgiCallable)
MiddleWareType = t.Union[
    WsgiCallableType,
    t.Tuple[WsgiCallableType],
    t.Tuple[WsgiCallableType, t.Dict[str, t.Any]],
]
BaseViewType = t.TypeVar("BaseViewType", bound=BaseView)
ViewType = t.Union[
    BaseViewType,
    t.Tuple[BaseViewType],
    t.Tuple[BaseViewType, t.Dict[str, t.Any]],
    t.Tuple[BaseViewType, Blueprint, t.Dict[str, t.Any]],
]


# pylint: disable=too-many-instance-attributes
class AppBuilder:
    conf_module = config
    app_name: str = config.FLASK_APP
    secret_file: str = config.SECRET_KEY_FILE_NAME
    flask_class: t.Type[flaskel.Flaskel] = flaskel.Flaskel
    url_converters: t.Dict[str, t.Type[BaseConverter]] = CONVERTERS

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        app: t.Optional[Flaskel] = None,
        *,
        conf_module: t.Optional[str] = None,
        views: t.Tuple[ViewType, ...] = (),
        folders: t.Tuple[StrPathLikeType, ...] = (),
        blueprints: t.Tuple[BlueprintType, ...] = (),
        middlewares: t.Tuple[MiddleWareType, ...] = (),
        extensions: t.Optional[t.Dict[str, t.Any]] = None,
        after_request: t.Tuple[AfterRequestCallable, ...] = (),
        before_request: t.Tuple[BeforeRequestCallable, ...] = (),
        after_create_hook: t.Optional[t.Callable[[None], None]] = None,
        converters: t.Optional[t.Dict[str, t.Type[BaseConverter]]] = None,
        version: t.Optional[str] = None,
        **options,
    ):
        """

        :param app: an instance of Flaskel
        :param conf_module: python module file
        :param converters: custom url converter mapping
        :param extensions: custom extension appended to defaults
        :param blueprints: list of application's blueprints
        :param folders: list of custom jinja2's template folders
        :param middlewares: list of wsgi middleware
        :param views: list of views to register
        :param after_request: list of functions to register after request
        :param before_request: list of functions to register before request
        :param after_create_callback: a function called after all components are registered
        :param options: passed to Flask class
        :param version: app version, may be used by extensions
        :return:
        """
        self._app = app
        self._version = version
        self._options = options or {}
        self._converters = converters or {}
        self._extensions = extensions or {}
        self._views = views
        self._folders = folders
        self._blueprints = blueprints
        self._middlewares = middlewares
        self._after_request = after_request
        self._before_request = before_request
        self._after_create_callback = after_create_hook
        self._conf_module = conf_module or self.conf_module

    @property
    def app(self):
        return self._app

    def generate_secret_key(self, secret_file, key_length):
        secret_key = random_string(key_length)

        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(secret_key)
            abs_file = os.path.abspath(secret_file)
            self._app.logger.warning(
                "new secret key generated: take care of this file: %s", abs_file
            )
        return secret_key

    def load_secret_key(self, secret_file):
        if not os.path.isfile(secret_file):
            return None

        with open(secret_file, "r", encoding="utf-8") as f:
            secret_key = f.read()
            self._app.logger.info("load secret key from: %s", secret_file)
        return secret_key

    def set_secret_key(self):
        secret_key = None
        key_length = self._app.config.SECRET_KEY_MIN_LENGTH or 256

        if not self._app.config.get("FLASK_ENV", "").lower().startswith("dev"):
            secret_file = self._app.config.SECRET_KEY
            if secret_file:
                secret_key = self.load_secret_key(secret_file) or secret_file
            else:
                secret_key = self.load_secret_key(self.secret_file)
                secret_key = secret_key or self.generate_secret_key(
                    self.secret_file, key_length
                )
        elif not self._app.config.SECRET_KEY:
            self._app.logger.debug("set secret key in development mode")
            secret_key = "fake_very_complex_string"

        self._app.config.SECRET_KEY = secret_key or self._app.config.SECRET_KEY
        if len(secret_key) < key_length:
            self._app.logger.warning("secret key length is less than: %s", key_length)

        if not self._app.config.JWT_SECRET_KEY:
            self._app.config.JWT_SECRET_KEY = self._app.config.SECRET_KEY

    def set_config(self, conf: t.Optional[t.Union[str, t.Dict[str, t.Any]]] = None):
        self._app.config.from_object(self._conf_module)
        if isinstance(conf, str):
            self._app.config.from_object(conf)
        else:
            self._app.config.from_mapping(**(conf or {}))
        self._app.config.from_envvar("APP_CONFIG_FILE", silent=True)

    @staticmethod
    def normalize_tuple(tokens: t.Union[t.Any, tuple]) -> t.Tuple[t.Any, t.Dict]:
        if not isinstance(tokens, tuple):
            return tokens, {}
        return tokens[0], tokens[1] if len(tokens) > 1 else {}

    def register_extensions(self):
        with self._app.app_context():
            for name, e in self._extensions.items():
                try:
                    ext, opt = self.normalize_tuple(e)
                    if not ext:
                        raise TypeError("extension could not be None or empty")
                except (TypeError, IndexError) as exc:
                    self._app.logger.warning(
                        "Invalid extension '%s' configuration '%s': %s", name, e, exc
                    )
                    continue

                ext.init_app(self._app, **opt)
                self._app.logger.debug(
                    "Registered extension '%s' with options: %s", name, opt
                )

        self._app.logger.debug("Dump flask extensions:")
        for k, v in self._app.extensions.items():
            self._app.logger.debug("Registered extension '%s': %s", k, v)

    def register_blueprints(self):
        for b in self._blueprints:
            bp, opt = self.normalize_tuple(b)
            self._app.register_blueprint(bp, **opt)
            self._app.logger.debug(
                "Registered blueprint '%s' with options: %s", bp.name, opt
            )

    def register_converters(self):
        self._app.url_map.converters.update(self.url_converters)
        self._app.url_map.converters.update(self._converters)
        for k, v in self._app.url_map.converters.items():
            self._app.logger.debug("Registered converter: '%s' = %s", k, v.__name__)

    def register_template_folders(self):
        loaders = [self._app.jinja_loader]

        for fsl in self._folders:
            loaders.append(FileSystemLoader(fsl))

        if self._folders:
            self._app.jinja_loader = ChoiceLoader(loaders)
            for f in self._folders:
                self._app.logger.debug("Registered template folder: '%s'", f)

    def register_middlewares(self):
        for m in self._middlewares:
            m, kwargs = self.normalize_tuple(m)
            if isinstance(m, BaseMiddleware):
                m.flask_app = self._app

            self._app.wsgi_app = m(self._app.wsgi_app, **kwargs)
            self._app.logger.debug("Registered middleware: '%s'", m.__name__)

    def register_views(self):
        def normalize_args(data: ViewType) -> tuple:
            if not isinstance(data, tuple):
                data = (data,)
            d = data + (None,) * (3 - len(data))
            if isinstance(d[1], dict):
                return d[0], d[2], d[1]
            return d[0], d[1], d[2] or {}

        def normalize_params(_v, _p: dict) -> dict:
            _p.setdefault("name", _v.default_view_name)
            _p.setdefault("urls", _v.default_urls)
            return _p

        for view in self._views:
            v, b, p = normalize_args(view)
            v.register(b or self._app, **normalize_params(v, p))
            mess = f"on blueprint '{b.name}'" if b else ""
            self._app.logger.debug(
                "Registered view: '%s' %s with params: %s", v.__name__, mess, p
            )

    def register_after_request(self):
        for f in self._after_request:
            self._app.after_request_funcs.setdefault(None, []).append(f)
            self._app.logger.debug(
                "Registered function after request: '%s'", f.__name__
            )

    def register_before_request(self):
        for f in self._before_request:
            self._app.before_request_funcs.setdefault(None, []).append(f)
            self._app.logger.debug(
                "Registered function before request: '%s'", f.__name__
            )

    def set_linter_and_profiler(self):
        if self._app.config.WSGI_WERKZEUG_PROFILER_ENABLED:
            file = self._app.config.WSGI_WERKZEUG_PROFILER_FILE
            self._app.wsgi_app = ProfilerMiddleware(
                self._app.wsgi_app,
                # pylint: disable=consider-using-with
                stream=open(file, "w", encoding="utf-8") if file else sys.stdout,
                restrictions=self._app.config.WSGI_WERKZEUG_PROFILER_RESTRICTION,
            )
            self._app.logger.debug("Registered: '%s'", ProfilerMiddleware.__name__)

        if self._app.config.WSGI_WERKZEUG_LINT_ENABLED:
            self._app.wsgi_app = LintMiddleware(self._app.wsgi_app)
            self._app.logger.debug("Registered: '%s'", LintMiddleware.__name__)

    def dump_urls(self):
        if self._app is not None:
            self._app.logger.debug("Registered routes:\n%s", DumpUrls(self._app))

    def init_db(self):
        try:
            sqlalchemy = self._app.extensions.get("sqlalchemy")
            if sqlalchemy is not None:
                register_engine_events(sqlalchemy.db.engine)
                sqlalchemy.db.create_all(app=self._app)
        except Exception as exc:  # pylint: disable=broad-except
            self._app.logger.exception(exc)

    def after_create_hook(self):
        self.dump_urls()

        if self._app.debug:
            self.set_linter_and_profiler()

        with self._app.app_context():
            self.init_db()
            if callable(self._after_create_callback):
                self._after_create_callback()

    def create(
        self, conf: t.Optional[t.Union[str, t.Dict[str, t.Any]]] = None
    ) -> Flaskel:
        self._app = self._app or self.flask_class(self.app_name, **self._options)
        self._app.version = self._version

        self.set_config(conf)
        self.set_secret_key()

        self.register_extensions()
        self.register_middlewares()
        self.register_template_folders()
        self.register_converters()
        self.register_views()
        self.register_blueprints()
        self.register_after_request()
        self.register_before_request()

        self.after_create_hook()
        return self._app
