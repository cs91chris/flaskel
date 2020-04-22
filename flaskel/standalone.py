import yaml
import click
from six import iteritems
from yaml.error import YAMLError

from .factory import default_app_factory

try:
    from gunicorn.app.base import BaseApplication
except ModuleNotFoundError:
    # only for windows or if you do not want gunicorn
    class BaseApplication:
        """
        on windows application must be in DEBUG
        """


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self.application = app
        self.options = options or {}
        super(StandaloneApplication, self).__init__()

    def init(self, parser, opts, args):
        """

        :param parser:
        :param opts:
        :param args:
        """
        pass

    def load_config(self):
        """

        """
        options = {}

        for k, v in iteritems(self.options):
            if k in self.cfg.settings and v is not None:
                options.update({k: v})

        for key, value in iteritems(options):
            self.cfg.set(key.lower(), value)

    def load(self):
        """

        :return:
        """
        return self.application


def serve_forever(factory=default_app_factory, application_class=StandaloneApplication, **kwargs):
    """

    :param factory:
    :param application_class:
    :param kwargs:
    :return:
    """
    @click.command()
    @click.option('-w', '--workers', default=2, help='number of workers')
    @click.option('-t', '--timeout', default=60, help='worker timeout')
    @click.option('-c', '--config',  default=None, help='yaml app configuration file')
    @click.option('-L', '--log-config', default=None, help='yaml log configuration file')
    @click.option('-b', '--bind', default='127.0.0.1:5000', help='address to bind')
    @click.option('-d', '--debug', default=False, help='enable debug mode')
    @click.option('-W', '--worker-class', default="egg:meinheld#gunicorn_worker", help='gunicorn worker class')
    def _serve_forever(workers, timeout, config, log_config, bind, debug, worker_class):
        """

        :param workers:
        :param timeout:
        :param config:
        :param log_config:
        :param bind:
        :param debug:
        :param worker_class:
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
            config = dict(
                app={
                    'DEBUG': debug,
                    'ENV':   'development' if debug else 'production'
                },
                wsgi={
                    'bind': bind,
                    'workers': workers,
                    'timeout': timeout,
                    'debug': debug,
                    'worker-class': worker_class
                }
            )

        if log_config is not None:
            config['app']['LOG_FILE_CONF'] = log_config

        kwargs['conf_map'] = config.get('app', {})
        _app = factory(**kwargs)

        if debug:
            _app.run(
                host=_app.config['APP_HOST'],
                port=_app.config['APP_PORT'],
                debug=_app.config['DEBUG']
            )
        else:
            application_class(_app, config.get('wsgi', {})).run()

    _serve_forever()
