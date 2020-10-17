import os

import click
import yaml

from flaskel import AppFactory
from flaskel.utils.misc import parse_value
from flaskel.wsgi import BaseApplication, WSGIFactory

wsgi_types = click.Choice(
    WSGIFactory.WSGI_SERVERS.keys(),
    case_sensitive=False
)


def option_as_dict(ctx, param, value):
    """

    :param ctx:
    :param param:
    :param value:
    :return:
    """
    ret = {}
    for opt in value:
        k, v = opt.split("=", 2)
        ret.update({k: parse_value(v)})
    return ret


class Server:
    opt_config_attr = dict(
        default=None,
        help='app yaml configuration file'
    )
    opt_log_config_attr = dict(
        default=None,
        help='alternative log yaml configuration file'
    )
    opt_bing_attr = dict(
        default='127.0.0.1:5000',
        help='address to bind',
        show_default=True
    )
    opt_debug_attr = dict(
        is_flag=True,
        flag_value=True,
        default=False,
        help='enable debug mode'
    )
    opt_wsgi_server_attr = dict(
        default=None,
        type=wsgi_types,
        help='name of wsgi server to use'
    )
    option_wsgi_config_attr = dict(
        default={},
        multiple=True,
        callback=option_as_dict,
        metavar="KEY=VAL",
        help='wsgi configuration'
    )

    def __init__(self, app_factory=AppFactory(), wsgi_factory=WSGIFactory()):
        """

        :param app_factory:
        :param wsgi_factory:
        """
        self._app_factory = app_factory
        self._wsgi_factory = wsgi_factory

        assert isinstance(self._app_factory, AppFactory)
        assert isinstance(self._wsgi_factory, WSGIFactory)

    def _register_options(self, func):
        """

        :param func:
        :return:
        """

        @click.command()
        @click.option('-b', '--bind', **self.opt_bing_attr)
        @click.option('-d', '--debug', **self.opt_debug_attr)
        @click.option('-c', '--config', **self.opt_config_attr)
        @click.option('-l', '--log-config', **self.opt_log_config_attr)
        @click.option('-w', '--wsgi-server', **self.opt_wsgi_server_attr)
        @click.option('-D', '--wsgi-config', **self.option_wsgi_config_attr)
        def _options(*args, **kwargs):
            return func(*args, **kwargs)

        return _options

    def run_from_cli(self, **kwargs):
        @self._register_options
        def _forever(config, log_config, bind, debug, wsgi_server, wsgi_config):
            self.serve_forever(
                bind=bind,
                debug=debug,
                config=config,
                log_config=log_config,
                wsgi_server=wsgi_server,
                wsgi_config=wsgi_config,
                **kwargs
            )

        return _forever()

    @staticmethod
    def _prepare_config(filename, **kwargs):
        """

        :param filename:
        :return: config
        """
        if filename is not None:
            with open(filename) as f:
                config = yaml.safe_load(f)
        else:
            env = os.environ.get('FLASK_ENV')
            env = env or ('development' if kwargs['debug'] else 'production')
            config = dict(
                app={'DEBUG': kwargs['debug'], 'ENV': env},
                wsgi={'bind': kwargs['bind'], 'debug': kwargs['debug']}
            )

        if kwargs['log_config'] is not None:
            config['app']['LOG_FILE_CONF'] = kwargs['log_config']

        # debug flag enabled overrides config file
        if kwargs['debug'] is True:
            config['app']['DEBUG'] = True

        return config

    def serve_forever(self, config=None, log_config=None, bind=None, debug=None,
                      wsgi_class=None, wsgi_server=None, wsgi_config=None):
        """

        :param config: app and wsgi configuration file
        :param log_config: log configuration file
        :param bind: address to bind
        :param debug: enable debug mode
        :param wsgi_class: optional a custom subclass of BaseApplication
        :param wsgi_server: wsgi server chose
        :param wsgi_config: wsgi configuration
        :return: never returns
        """
        config = self._prepare_config(config, debug=debug, bind=bind, log_config=log_config)
        wsgi_config = {**(wsgi_config or {}), **(config.get('wsgi') or {})}

        if wsgi_server:
            wsgi_class = self._wsgi_factory.getClass(wsgi_server)
        elif wsgi_class is None:
            wsgi_class = self._wsgi_factory.getClass('builtin')

        assert issubclass(wsgi_class, BaseApplication)

        app = self._app_factory.get_or_create(config.get('app'))
        wsgi = wsgi_class(app, options=wsgi_config)
        wsgi.run()  # run forever
