from collections import namedtuple

import click
import yaml
from yaml.error import YAMLError
from six import iteritems

from app import create_app

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


Args = namedtuple('Args', (
        'workers',
        'timeout',
        'config',
        'log_config',
        'bind',
        'debug',
        'worker_class',
    ))


def main(args: Args):
    """

    :param args:
    :return:
    """
    if args.config is not None:
        try:
            with open(args.config) as f:
                config = yaml.safe_load(f)
        except (OSError, YAMLError) as e:
            import sys
            print(e, file=sys.stderr)
            sys.exit(1)
    else:
        config = dict(
            app={
                'DEBUG': args.debug,
                'ENV': 'development' if args.debug else 'production'
            },
            wsgi={
                'bind': args.bind,
                'workers': args.workers,
                'timeout': args.timeout,
                'debug': args.debug,
                'worker-class': args.worker_class
            }
        )

    if args.log_config is not None:
        config['app']['LOG_FILE_CONF'] = args.log_config

    _app = create_app(conf_map=config.get('app', {}))

    if args.debug:
        return _app

    return StandaloneApplication(_app, config.get('wsgi', {}))


@click.command()
@click.option('-w', '--workers', default=2, help='number of workers')
@click.option('-t', '--timeout', default=60, help='worker timeout')
@click.option('-c', '--config',  default=None, help='yaml app configuration file')
@click.option('-L', '--log-config', default=None, help='yaml log configuration file')
@click.option('-b', '--bind', default='127.0.0.1:5000', help='address to bind')
@click.option('-d', '--debug', default=False, help='enable debug mode')
@click.option('-W', '--worker-class', default="egg:meinheld#gunicorn_worker", help='gunicorn worker class')
def cli(workers, timeout, config, log_config, bind, debug, worker_class):
    main(Args(
        workers=workers,
        timeout=timeout,
        config=config,
        log_config=log_config,
        bind=bind,
        debug=debug,
        worker_class=worker_class
    )).run()


if __name__ == '__main__':
    cli()
