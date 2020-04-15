import flask
import jinja2

from flaskel.config import FLASK_APP
from flaskel.converters import CONVERTERS


def bootstrap(conf_module=None, conf_map=None, converters=None,
              extensions=None, blueprints=None, template_folders=None, **kwargs):
    """

    :param conf_module: python module file
    :param conf_map: mapping configuration
    :param converters: custom url converter mapping
    :param extensions: custom extension appended to defaults
    :param blueprints: list of application's blueprints
    :param template_folders: list of custom jinja2's template folders
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
        except (TypeError, IndexError) as exc:
            app.logger.debug(str(exc))
            continue

        with app.app_context():
            ex.init_app(app, **opt)
            app.logger.debug("Registered extension '%s' with options: %s", ext_name, str(opt))

    for b in (blueprints or []):
        try:
            bp = b[0]
            opt = b[1] if len(b) > 1 else {}
        except (TypeError, IndexError) as exc:
            app.logger.debug(str(exc))
            continue

        app.register_blueprint(bp, **opt)
        app.logger.debug("Registered blueprint '%s' with options: %s", bp.name, str(opt))

    app.logger.debug("Registered converters\n{}".format(app.url_map.converters))

    if template_folders:
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader(template_folders),
        ])
        app.logger.debug("Registered template folders\n{}".format(", ".join(template_folders)))

    return app
