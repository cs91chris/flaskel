from flask import Flask

from ext import errors
from ext import logger

from flaskel.config import FLASK_APP


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

    logger.init_app(app)
    errors.init_app(app)

    for e in (ext or ()):
        ex = e[0]
        opt = e[1] if len(e) > 1 else {}
        ext_name = ex.__class__.__name__
        ex.init_app(app, **opt)
        app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))

    for b in (bp or ()):
        bp = b[0]
        opt = b[1] if len(b) > 1 else {}
        app.register_blueprint(bp, **opt)
        app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))

    return app
