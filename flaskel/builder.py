import os
import sys

import jinja2
from werkzeug.middleware.lint import LintMiddleware
from werkzeug.middleware.profiler import ProfilerMiddleware

from . import config, flaskel
from .converters import CONVERTERS
from .utils import misc, ObjectDict


class AppBuilder:
    """Flask app builder"""

    """

    default app name
    """
    app_name = config.FLASK_APP

    """
    default secret key file name
    """
    secret_file = '.secret.key'

    """
    custom url converters
    """
    url_converters = CONVERTERS

    """
    custom app config module
    """
    conf_module = config

    def __init__(self, conf_module=None, extensions=None, converters=None,
                 blueprints=None, folders=None, middlewares=None, views=None,
                 after_request=None, before_request=None, callback=None, **options):
        """

        :param conf_module: python module file
        :param converters: custom url converter mapping
        :param extensions: custom extension appended to defaults
        :param blueprints: list of application's blueprints
        :param folders: list of custom jinja2's template folders
        :param middlewares: list of wsgi middleware
        :param views: list of views to register
        :param after_request: list of functions to register after request
        :param before_request: list of functions to register before request
        :param callback: a function called to patch app after all components registration
        :param options: passed to Flask class
        :return:
        """
        self._app = None
        self._converters = converters or {}
        self._blueprints = blueprints or ()
        self._extensions = extensions or {}
        self._middlewares = middlewares or ()
        self._folders = folders or ()
        self._options = options or ()
        self._views = views or ()
        self._after_request = after_request or ()
        self._before_request = before_request or ()
        self._callback = callback or (lambda: None)
        self._conf_module = conf_module or self.conf_module

    def _generate_secret_key(self, secret_file, key_length):
        secret_key = misc.random_string(key_length)

        with open(secret_file, 'w') as f:
            f.write(secret_key)
            abs_file = os.path.abspath(secret_file)
            self._app.logger.warning(f"new secret key generated: take care of this file: {abs_file}")
        return secret_key

    def _load_secret_key(self, secret_file):
        if not os.path.isfile(secret_file):
            return None

        with open(secret_file, 'r') as f:
            secret_key = f.read()
            self._app.logger.info(f"load secret key from: {secret_file}")
        return secret_key

    def _set_secret_key(self):
        secret_key = None
        key_length = self._app.config.SECRET_KEY_MIN_LENGTH

        if not self._app.config.get('FLASK_ENV', '').lower().startswith('dev'):
            secret_file = self._app.config.SECRET_KEY

            if secret_file:
                secret_key = self._load_secret_key(secret_file) or secret_file
            else:
                secret_file = self.secret_file
                secret_key = self._load_secret_key(secret_file)
                secret_key = secret_key or self._generate_secret_key(secret_file, key_length)
        elif not self._app.config.get('SECRET_KEY'):
            self._app.logger.debug('set secret key in development mode')
            secret_key = 'fake_very_complex_string'

        self._app.config.SECRET_KEY = secret_key or self._app.config.SECRET_KEY
        if len(secret_key) < key_length:
            self._app.logger.warning(f"secret key length is less than: {key_length}")

    def _register_extensions(self):
        with self._app.app_context():
            for name, e in self._extensions.items():
                try:
                    ext, opt = e[0], e[1] if len(e) > 1 else {}
                    if not ext:
                        raise TypeError("extension could not be None")
                except (TypeError, IndexError) as exc:
                    self._app.logger.debug(f"Invalid extension '{name}' configuration '{e}': {exc}")
                    continue

                ext.init_app(self._app, **opt)
                self._app.logger.debug(f"Registered extension '{name}' with options: {opt}")

        self._app.logger.debug(f"Dump flask extensions:")
        for k, v in self._app.extensions.items():
            self._app.logger.debug(f"Registered extension '{k}': {v}")

    def _register_blueprints(self):
        for b in self._blueprints:
            try:
                bp, opt = b[0], b[1] if len(b) > 1 else {}
                if not bp:
                    raise TypeError('blueprint could not be None')
            except (TypeError, IndexError) as exc:
                self._app.logger.debug(f"invalid blueprint configuration '{b}': {exc}")
                continue

            self._app.register_blueprint(bp, **opt)
            self._app.logger.debug(f"Registered blueprint '{bp.name}' with options: {opt}")

    def _set_config(self, conf):
        self._app.config.from_object(self._conf_module)
        self._app.config.from_mapping(**(conf or {}))
        self._app.config.from_envvar('APP_CONFIG_FILE', silent=True)
        self._app.config = ObjectDict(**self._app.config)

    def _register_converters(self):
        conv = {**self.url_converters, **self._converters}
        self._app.url_map.converters.update(conv)

        for k, v in conv.items():
            self._app.logger.debug(f"Registered converter: '{k}' = {v.__name__}")

    def _register_template_folders(self):
        loaders = [self._app.jinja_loader]

        for fsl in self._folders:
            loaders.append(jinja2.FileSystemLoader(fsl))

        if self._folders:
            self._app.jinja_loader = jinja2.ChoiceLoader(loaders)
            for f in self._folders:
                self._app.logger.debug(f"Registered template folder: '{f}'")

    def _register_middlewares(self):
        for m in self._middlewares:
            # WorkAround: in order to pass flask app to middleware without breaking chain
            if not (hasattr(m, 'flask_app') and m.flask_app):
                setattr(m, 'flask_app', self._app)

            self._app.wsgi_app = m(self._app.wsgi_app)
            self._app.logger.debug(f"Registered middleware: '{m.__name__}'")

    def _register_views(self):
        def normalize(data):
            d = data + (None,) * (3 - len(data))
            if isinstance(d[1], dict):
                return d[0], d[2], d[1]
            return d[0], d[1], d[2] or {}

        for view in self._views:
            v, b, p = normalize(view)
            v.register(b or self._app, **p)
            mess = f"on blueprint '{b.name}'" if b else ""
            self._app.logger.debug(f"Registered view: '{v.__name__}' {mess} with params: {p}")

    def _register_after_request(self):
        for f in self._after_request:
            self._app.after_request_funcs.setdefault(None, []).append(f)
            self._app.logger.debug(f"Registered function after request: '{f.__name__}'")

    def _register_before_request(self):
        for f in self._before_request:
            self._app.before_request_funcs.setdefault(None, []).append(f)
            self._app.logger.debug(f"Registered function before request: '{f.__name__}'")

    def _set_linter_and_profiler(self):
        if self._app.config.WSGI_WERKZEUG_LINT_ENABLED:
            self._app.wsgi_app = LintMiddleware(self._app.wsgi_app)
            self._app.logger.debug(f"Registered middleware: '{LintMiddleware.__name__}'")

        if self._app.config.WSGI_WERKZEUG_PROFILER_ENABLED:
            file = self._app.config.WSGI_WERKZEUG_PROFILER_FILE
            self._app.wsgi_app = ProfilerMiddleware(
                self._app.wsgi_app,
                stream=open(file, 'w') if file else sys.stdout,
                restrictions=self._app.config.WSGI_WERKZEUG_PROFILER_RESTRICTION
            )
            self._app.logger.debug(f"Registered middleware: '{ProfilerMiddleware.__name__}'")

    def _dump_urls(self):
        output = []
        for rule in self._app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            output.append("{:30s} {:40s} {}".format(rule.endpoint, methods, rule))

        lines = "\n".join(sorted(output))
        self._app.logger.debug(f"Registered routes:\n{lines}")

    def _patch_app(self):
        if self._app.debug:
            self._set_linter_and_profiler()
            self._dump_urls()

        @self._app.before_first_request
        def create_database():
            sqlalchemy = self._app.extensions.get('sqlalchemy')
            if sqlalchemy is not None:
                sqlalchemy.db.create_all()

        self._callback()

    def create(self, conf=None):
        self._app = flaskel.Flaskel(self.app_name, **self._options)

        self._set_config(conf)
        self._set_secret_key()

        self._register_extensions()
        self._register_middlewares()
        self._register_template_folders()
        self._register_converters()
        self._register_views()
        self._register_blueprints()
        self._register_after_request()
        self._register_before_request()

        self._patch_app()

    def get_or_create(self, conf=None):
        if self._app is None:
            self.create(conf)

        return self._app
