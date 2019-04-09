from flask import Flask

from flaskel.config import FLASK_APP

from ext import EXTENSIONS
from blueprints import BLUEPRINTS


def bootstrap(conf_module=None, **kwargs):
    """

    :param conf_module:
    :param kwargs:
    :return:
    """
    app = Flask(FLASK_APP, **kwargs)

    app.config.from_object(conf_module or 'flaskel.config')
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    for e in EXTENSIONS:
        ex = e[0]
        opt = e[1] if len(e) > 1 else {}
        ext_name = ex.__class__.__name__
        ex.init_app(app, **opt)
        app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))

    for b in BLUEPRINTS:
        bp = b[0]
        opt = b[1] if len(b) > 1 else {}
        app.register_blueprint(bp, **opt)
        app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))

    return app
