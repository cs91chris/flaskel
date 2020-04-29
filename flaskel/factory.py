import os
import string
from random import SystemRandom

import flask
import jinja2
from flask_response_builder import encoders
from werkzeug.middleware.lint import LintMiddleware
from werkzeug.middleware.profiler import ProfilerMiddleware

from .config import FLASK_APP
from .converters import CONVERTERS
from .patch import ReverseProxied, HTTPMethodOverride


def set_secret_key(app):
    """

    :param app: Flask instance
    """
    if not app.config.get('FLASK_ENV', '').lower().startswith('dev'):
        secret_file = app.config.get('SECRET_KEY')
        key_length = app.config['SECRET_KEY_MIN_LENGTH']

        if secret_file:
            if os.path.isfile(secret_file):
                with open(secret_file, 'r') as f:
                    app.config['SECRET_KEY'] = f.read()
                    app.logger.info("load secret key from: {}".format(secret_file))
            else:
                app.logger.warning("secret key length is less than: {}".format(key_length))
                app.config['SECRET_KEY'] = secret_file

            if len(app.config['SECRET_KEY']) > key_length:
                app.logger.warning("secret key length is less than: {}".format(key_length))
        else:
            secret_file = '.secret.key'
            if os.path.isfile(secret_file):
                app.logger.info("found file '{}' it is used as secret key".format(secret_file))
                with open(secret_file, 'r') as f:
                    secret_key = f.read()
            else:
                alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
                secret_key = ''.join(SystemRandom().choice(alphabet) for _ in range(key_length))
                with open(secret_file, 'w') as f:
                    f.write(secret_key)
                    app.logger.warning(
                        "new secret key generated: take care of this file:{}".format(secret_file)
                    )
            app.config['SECRET_KEY'] = secret_key
    elif not app.config.get('SECRET_KEY'):
        app.logger.debug('set secret key in development mode')
        app.config['SECRET_KEY'] = 'very_complex_string'
    else:
        app.logger.debug('given secret key: "{}"'.format(app.config.get('SECRET_KEY')))


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
        _app.wsgi_app = LintMiddleware(_app.wsgi_app)
        _app.wsgi_app = ProfilerMiddleware(_app.wsgi_app)

    _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    _app.json_encoder = encoders.JsonEncoder
    return _app
