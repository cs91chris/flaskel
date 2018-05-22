from flask import Flask

from flaskel.ext import errors
from flaskel.ext import logger

from flaskel.config import FLASK_APP


def register_blueprint(app, blueprint, prefix=None):
    """

    :param app:
    :param blueprint:
    :param prefix:
    """
    if prefix is not None:
        app.register_blueprint(blueprint, url_prefix=prefix)
        app.logger.debug("Registered blueprint '%s' with prefix '%s'", blueprint.name, prefix)
    else:
        app.register_blueprint(blueprint)
        app.logger.debug("Registered blueprint '%s' without prefix", blueprint.name)


def bootstrap(conf_module=None, ext=None, bp=None, **kwargs):
    """

    :param conf_module:
    :param ext:
    :param bp:
    :param kwargs:
    :return:
    """
    app = Flask(FLASK_APP, **kwargs)

    app.config.from_object(conf_module or 'flaskel.config')
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)
    app.config.setdefault('LOG_LOGGER_NAME', app.config.get('FLASK_ENV'))
    app.config.setdefault('LOG_APP_NAME', app.config.get('APP_NAME'))

    logger.init_app(app)
    errors.init_app(app)
    errors.api_register(app)

    for ext in (ext or ()):
        ext.init_app(app)

    for b in (bp or ()):
        register_blueprint(app, *b)

    return app

