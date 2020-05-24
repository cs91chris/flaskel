import os

import yaml
from yaml.error import YAMLError

from .factory import default_app_factory
from .wsgi import BaseApplication, wsgi_factory


def serve_forever(app=None, factory=default_app_factory, wsgi_class=None,
                  config=None, log_config=None, bind=None, debug=None, wsgi_server=None, **kwargs):
    """

    :param app: given app instance
    :param factory: optional a custom flask app factory function
    :param wsgi_class: optional a custom subclass of BaseApplication
    :param config: app and wsgi configuration file
    :param log_config: log configuration file
    :param bind: address to bind
    :param debug: enable debug mode
    :param wsgi_server: wsgi server chose
    :param kwargs: parameters passed to factory
    :return: never returns
    """
    if config is not None:
        try:
            with open(config) as f:
                config = yaml.safe_load(f)
        except (OSError, YAMLError) as e:
            import sys
            print(e, file=sys.stderr)
            sys.exit(1)
    else:
        env = os.environ.get('FLASK_ENV')
        config = dict(
            app={
                'DEBUG': debug,
                'ENV': env or ('development' if debug else 'production')
            },
            wsgi={
                'bind': bind,
                'debug': debug,
            }
        )

    if log_config is not None:
        config['app']['LOG_FILE_CONF'] = log_config

    # debug flag enabled overrides config file
    if debug is True:
        config['app']['DEBUG'] = True

    kwargs['conf_map'] = config.get('app', {})
    _app = factory(**kwargs) if not app else app

    if not wsgi_server:
        if wsgi_class:
            if not issubclass(wsgi_class, BaseApplication):
                raise TypeError('{} must be subclass of {}'.format(
                    wsgi_class.__name__,
                    BaseApplication.__name__
                ))
        else:
            wsgi_class = wsgi_factory('builtin')
    else:
        wsgi_class = wsgi_factory(wsgi_server)

    wsgi_class(_app, options=config.get('wsgi', {})).run()
