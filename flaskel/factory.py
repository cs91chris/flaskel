import os
import string
import sys
from random import SystemRandom

import flask
import jinja2
from flask_response_builder import encoders
from werkzeug.middleware.lint import LintMiddleware
from werkzeug.middleware.profiler import ProfilerMiddleware

from .config import FLASK_APP
from .converters import CONVERTERS
from .patch import HTTPMethodOverride, ReverseProxied


class AppFactory:
    """Flask app factory"""

    """
    default app name
    """
    app_name = FLASK_APP

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
    conf_module = 'flaskel.config'

    """
    additional wsgi middlewares
    """
    middlewares = [HTTPMethodOverride, ReverseProxied]

    """
    additional options
    """
    options = {
        "json_encoder": encoders.JsonEncoder
    }

    def __init__(self):
        """

        """
        self._app = None

    def generate_secret_key(self, secret_file, key_length):
        """

        :param secret_file:
        :param key_length:
        """
        alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
        secret_key = ''.join(SystemRandom().choice(alphabet) for _ in range(key_length))

        with open(secret_file, 'w') as f:
            f.write(secret_key)
            abs_file = os.path.abspath(secret_file)
            mess = "new secret key generated: take care of this file:{}"
            self._app.logger.warning(mess.format(abs_file))
        return secret_key

    def load_secret_key(self, secret_file):
        """

        :param secret_file:
        :return:
        """
        if not os.path.isfile(secret_file):
            return None

        with open(secret_file, 'r') as f:
            secret_key = f.read()
            self._app.logger.info("load secret key from: {}".format(secret_file))
        return secret_key

    def set_secret_key(self):
        """

        """
        secret_key = None
        key_length = self._app.config['SECRET_KEY_MIN_LENGTH']

        if not self._app.config.get('FLASK_ENV', '').lower().startswith('dev'):
            secret_file = self._app.config.get('SECRET_KEY')

            if secret_file:
                secret_key = self.load_secret_key(secret_file) or secret_file
            else:
                secret_file = self.secret_file
                secret_key = self.load_secret_key(secret_file)
                secret_key = secret_key or self.generate_secret_key(secret_file, key_length)
        elif not self._app.config.get('SECRET_KEY'):
            self._app.logger.debug('set secret key in development mode')
            secret_key = 'fake_very_complex_string'

        self._app.config['SECRET_KEY'] = secret_key or self._app.config['SECRET_KEY']
        if len(secret_key) < key_length:
            self._app.logger.warning("secret key length is less than: {}".format(key_length))

    def register_extensions(self, extensions):
        """

        :param extensions: custom extension added to defaults
        """
        with self._app.app_context():
            for name, e in (extensions or {}).items():
                try:
                    ext = e[0]
                    opt = e[1] if len(e) > 1 else {}
                    if not ext:
                        raise TypeError("extension could not be None")
                except (TypeError, IndexError) as exc:
                    mess = "Invalid extension '{}' configuration '{}':\n{}"
                    self._app.logger.debug(mess.format(name, e, exc))
                    continue

                ext.init_app(self._app, **opt)
                mess = "Registered extension '{}' with options: {}"
                self._app.logger.debug(mess.format(name, str(opt)))

    def register_blueprints(self, blueprints):
        """

        :param blueprints: list of application's blueprints
        """
        for b in (blueprints or []):
            try:
                bp = b[0]
                opt = b[1] if len(b) > 1 else {}
                if not bp:
                    raise TypeError('blueprint could not be None')
            except (TypeError, IndexError) as exc:
                self._app.logger.debug("invalid blueprint configuration '{}':\n{}".format(b, exc))
                continue

            self._app.register_blueprint(bp, **opt)
            self._app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))

    def set_config(self, conf_module=None, conf_map=None):
        """

        :param conf_module:
        :param conf_map:
        :return:
        """
        self._app.config.from_object(conf_module or self.conf_module)
        self._app.config.from_mapping(**(conf_map or {}))
        self._app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    def register_converters(self, converters):
        """

        :param converters:
        """
        conv = {**self.url_converters, **(converters or {})}
        self._app.url_map.converters.update(conv)

        for k in conv.keys():
            self._app.logger.debug("Registered converter: '{}'".format(k))

    def register_template_folders(self, folders=()):
        """

        :param folders:
        """
        loaders = [self._app.jinja_loader]

        for fsl in folders:
            loaders.append(jinja2.FileSystemLoader(fsl))

        self._app.jinja_loader = jinja2.ChoiceLoader(loaders)
        self._app.logger.debug("Registered template folders: '{}'".format(", ".join(folders)))

    def register_middlewares(self, middlewares):
        """

        :param middlewares:
        """
        middles = self.middlewares + (middlewares or [])
        for middleware in middles:
            self._app.wsgi_app = middleware(self._app.wsgi_app)
            self._app.logger.debug("Registered middleware: '{}'".format(middleware))

    def patch_app(self):
        """

        :return:
        """
        encoder = self.options.get('json_encoders')
        if encoder:
            self._app.json_encoder = encoder

        @self._app.before_first_request
        def create_database():
            sqla = self._app.extensions.get('sqlalchemy')
            if sqla is not None:
                sqla.db.create_all()

    def create(self, conf_module=None, conf_map=None, extensions=None,
               converters=(), blueprints=(), folders=(), middlewares=(), **kwargs):
        """

        :param conf_module: python module file
        :param conf_map: mapping configuration
        :param converters: custom url converter mapping
        :param extensions: custom extension appended to defaults
        :param blueprints: list of application's blueprints
        :param middlewares: list of wsgi middleware
        :param folders: list of custom jinja2's template folders
        :param kwargs: passed to Flask class
        :return:
        """
        self._app = flask.Flask(self.app_name, **kwargs)

        self.set_config(conf_module, conf_map)
        self.set_secret_key()

        self.register_template_folders(folders)
        self.register_converters(converters)
        self.register_extensions(extensions)
        self.register_blueprints(blueprints)
        self.register_middlewares(middlewares)

        self.patch_app()

    def getOrCreate(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        if self._app is not None:
            return self._app

        self.create(**kwargs)

        if self._app.config.get('DEBUG'):
            if self._app.config['WSGI_WERKZEUG_LINT_ENABLED']:
                self._app.wsgi_app = LintMiddleware(self._app.wsgi_app)

            if self._app.config['WSGI_WERKZEUG_PROFILER_ENABLED']:
                stream = self._app.config['WSGI_WERKZEUG_PROFILER_FILE']
                if stream:
                    stream = open(self._app.config['WSGI_WERKZEUG_PROFILER_FILE'], 'w')
                else:
                    stream = sys.stdout
            else:
                stream = None

            self._app.wsgi_app = ProfilerMiddleware(
                self._app.wsgi_app,
                stream=stream,
                restrictions=self._app.config['WSGI_WERKZEUG_PROFILER_RESTRICTION']
            )

        return self._app
