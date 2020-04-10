from flask import Flask

from ext import EXTENSIONS
from blueprints import BLUEPRINTS
from flaskel.config import FLASK_APP
from flaskel.converters import CONVERTERS


def bootstrap(conf_module=None, conf_map=None, converters=None, **kwargs):
    """

    :param conf_module: python module file
    :param conf_map: mapping configuration
    :param converters: custom url converter mapping
    :param kwargs: passed to Flask class
    :return:
    """
    app = Flask(FLASK_APP, **kwargs)

    # default configuration python module file
    app.config.from_object(conf_module or 'flaskel.config')

    # mapping configuration given
    app.config.from_mapping(**(conf_map or {}))

    # configuration from environ overrides configuration from files
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    app.url_map.converters.update(CONVERTERS)
    app.url_map.converters.update(converters or {})

    for e in EXTENSIONS:
        ex = e[0]
        opt = e[1] if len(e) > 1 else {}
        ext_name = ex.__class__.__name__

        with app.app_context():
            ex.init_app(app, **opt)
            app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))

    for b in BLUEPRINTS:
        bp = b[0]
        opt = b[1] if len(b) > 1 else {}
        app.register_blueprint(bp, **opt)
        app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))

    return app
