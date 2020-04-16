import flask
import jinja2

from flaskel.config import FLASK_APP
from flaskel.converters import CONVERTERS


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

    # configuration from environ overrides overrides all others
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    app.url_map.converters.update(CONVERTERS)
    app.url_map.converters.update(converters or {})

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

        with app.app_context():
            ex.init_app(app, **opt)
            app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))

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

    app.logger.debug("Registered converters\n{}".format(app.url_map.converters))

    if jinja_fs_loader:
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader(jinja_fs_loader),
        ])
        app.logger.debug("Registered template folders\n{}".format(", ".join(jinja_fs_loader)))

    return app
