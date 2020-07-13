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


def generate_secret_key(app, secret_file, key_length):
    """

    :param app:
    :param secret_file:
    :param key_length:
    """
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    secret_key = ''.join(SystemRandom().choice(alphabet) for _ in range(key_length))

    with open(secret_file, 'w') as f:
        f.write(secret_key)
        abs_file = os.path.abspath(secret_file)
        app.logger.warning(
            "new secret key generated: take care of this file:{}".format(abs_file)
        )
    return secret_key


def load_secret_key(app, secret_file):
    """

    :param app:
    :param secret_file:
    :return:
    """
    with open(secret_file, 'r') as f:
        secret_key = f.read()
        app.logger.info("load secret key from: {}".format(secret_file))
    return secret_key


def set_secret_key(app):
    """

    """
    secret_key = None
    key_length = app.config['SECRET_KEY_MIN_LENGTH']

    if not app.config.get('FLASK_ENV', '').lower().startswith('dev'):
        secret_file = app.config.get('SECRET_KEY')

        if secret_file:
            if os.path.isfile(secret_file):
                secret_key = load_secret_key(app, secret_file)
            else:
                secret_key = secret_file
        else:
            secret_file = '.secret.key'
            if os.path.isfile(secret_file):
                secret_key = load_secret_key(app, secret_file)
            else:
                secret_key = generate_secret_key(app, secret_file, key_length)
    elif not app.config.get('SECRET_KEY'):
        app.logger.debug('set secret key in development mode')
        secret_key = 'very_complex_string'

    app.config['SECRET_KEY'] = secret_key or app.config['SECRET_KEY']
    if len(secret_key) > key_length:
        app.logger.warning("secret key length is less than: {}".format(key_length))


def register_extensions(app, extensions):
    """

    :param app: Flask instance
    :param extensions: custom extension appended to defaults
    """
    with app.app_context():
        for e in (extensions or []):
            try:
                ex = e[0]
                opt = e[1] if len(e) > 1 else {}
                ext_name = ex.__class__.__name__
                if not ex:
                    raise TypeError('extension could not be None')
            except (TypeError, IndexError) as exc:
                app.logger.debug("invalid extension configuration '{}':\n{}".format(e, exc))
                continue

            ex.init_app(app, **opt)
            app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))


def register_blueprints(app, blueprints):
    """

    :param app: Flask instance
    :param blueprints: list of application's blueprints
    """
    for b in (blueprints or []):
        try:
            bp = b[0]
            opt = b[1] if len(b) > 1 else {}
            if not bp:
                raise TypeError('blueprint could not be None')
        except (TypeError, IndexError) as exc:
            app.logger.debug("invalid blueprint configuration '{}':\n{}".format(b, exc))
            continue

        app.register_blueprint(bp, **opt)
        app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))


def bootstrap(conf_module=None, conf_map=None, converters=None,
              extensions=None, blueprints=None, jinja_fs_loader=None, **kwargs):
    """

    :param conf_module: python module file
    :param conf_map: mapping configuration
    :param converters: custom url converter mapping
    :param extensions: custom extension appended to defaults
    :param blueprints: list of application's blueprints
    :param jinja_fs_loader: list of custom jinja2's template folders
    :param kwargs: passed to Flask class
    :return:
    """
    app = flask.Flask(FLASK_APP, **kwargs)

    app.config.from_object(conf_module or 'flaskel.config')
    app.config.from_mapping(**(conf_map or {}))
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    app.url_map.converters.update(CONVERTERS)
    app.url_map.converters.update(converters or {})

    set_secret_key(app)
    register_extensions(app, extensions)
    register_blueprints(app, blueprints)

    if jinja_fs_loader:
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader(jinja_fs_loader),
        ])
        app.logger.debug("Registered template folders\n{}".format(", ".join(jinja_fs_loader)))

    return app


def default_app_factory(**kwargs):
    """

    :param kwargs:
    :return:
    """
    _app = bootstrap(**kwargs)

    if _app.config.get('DEBUG'):
        if _app.config['WSGI_WERKZEUG_PROFILER_ENABLED']:
            stream = _app.config['WSGI_WERKZEUG_PROFILER_FILE']
            if stream:
                stream = open(_app.config['WSGI_WERKZEUG_PROFILER_FILE'], 'w')
            else:
                stream = sys.stdout
        else:
            stream = None

        _app.wsgi_app = ProfilerMiddleware(
            _app.wsgi_app,
            stream=stream,
            restrictions=_app.config['WSGI_WERKZEUG_PROFILER_RESTRICTION']
        )

        if _app.config['WSGI_WERKZEUG_LINT_ENABLED']:
            _app.wsgi_app = LintMiddleware(_app.wsgi_app)

    if _app.config['WSGI_REVERSE_PROXY_ENABLED']:
        _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    if _app.config['WSGI_METHOD_OVERRIDE_ENABLED']:
        _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    _app.json_encoder = encoders.JsonEncoder
    return _app
