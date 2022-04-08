import os
import typing as t

import click
from vbcore import yaml
from vbcore.datastruct import ObjectDict
from vbcore.misc import parse_value

from .builder import AppBuilder
from .config import config as configurator
from .wsgi import BaseApplication, DEFAULT_WSGI_SERVERS, WSGIFactory


def option_as_dict(ctx, param, value):
    _ = ctx, param
    ret = {}
    for opt in value:
        k, v = opt.split("=", 2)
        ret.update({k: parse_value(v)})
    return ret


class Server:
    opt_config_attr = dict(default=None, help="app yaml/json configuration file")
    opt_log_config_attr = dict(
        default=None, help="alternative log yaml/json configuration file"
    )
    opt_bing_attr = dict(
        default="127.0.0.1:5000", help="address to bind", show_default=True
    )
    opt_debug_attr = dict(
        is_flag=True, flag_value=True, default=False, help="enable debug mode"
    )
    opt_wsgi_server_attr = dict(
        default=None,
        type=click.Choice(list(DEFAULT_WSGI_SERVERS.keys()), case_sensitive=False),
        help="name of wsgi server to use",
    )
    option_wsgi_config_attr = dict(
        default={},
        multiple=True,
        callback=option_as_dict,
        metavar="KEY=VAL",
        help="wsgi configuration",
    )
    option_app_config_attr = dict(
        default={},
        multiple=True,
        callback=option_as_dict,
        metavar="KEY=VAL",
        help="app configuration",
    )

    def __init__(
        self,
        app_factory: t.Optional[AppBuilder] = None,
        wsgi_factory: t.Optional[WSGIFactory] = None,
    ):
        self._app_factory = app_factory or AppBuilder()
        self._wsgi_factory = wsgi_factory or WSGIFactory(
            base_class=BaseApplication, classes=DEFAULT_WSGI_SERVERS
        )

    def register_options(self, func: t.Callable) -> t.Callable:
        @click.command()
        @click.option("-b", "--bind", **self.opt_bing_attr)
        @click.option("-d", "--debug", **self.opt_debug_attr)
        @click.option("-c", "--config", **self.opt_config_attr)
        @click.option("-l", "--log-config", **self.opt_log_config_attr)
        @click.option("-w", "--wsgi-server", **self.opt_wsgi_server_attr)
        @click.option("-D", "--wsgi-config", **self.option_wsgi_config_attr)
        @click.option("-W", "--app-config", **self.option_app_config_attr)
        def callable_options(*args, **kwargs):
            return func(*args, **kwargs)

        return callable_options

    def run_from_cli(self, **kwargs):
        self.runner(**kwargs)

    def runner(self, **kwargs) -> t.Callable:
        @self.register_options
        def forever(**params):
            self.serve_forever(**params, **kwargs)

        return forever

    @staticmethod
    def prepare_config(
        filename: str,
        debug: bool = False,
        bind: t.Optional[str] = None,
        log_config: t.Optional[str] = None,
    ):
        default_env = "development" if debug else "production"
        env = configurator("FLASK_ENV", default=default_env)

        if filename is not None:
            config = yaml.load_yaml_file(filename)
            if not config.app.FLASK_ENV:
                config.app.FLASK_ENV = env
        else:
            config = ObjectDict(
                app={"DEBUG": debug, "FLASK_ENV": env},
                wsgi={"bind": bind, "debug": debug},
            )

        if log_config is not None:
            config.app.LOG_FILE_CONF = log_config

        # debug flag enabled overrides config file
        if debug is True:
            config.app.DEBUG = True
            os.environ["FLASK_DEBUG"] = "1"
        if bind is not None:
            config.wsgi.bind = bind

        os.environ["FLASK_ENV"] = config.app.FLASK_ENV
        return config

    def serve_forever(
        self,
        config: t.Optional[str] = None,
        log_config: t.Optional[str] = None,
        bind: t.Optional[str] = None,
        wsgi_class: t.Type[BaseApplication] = None,
        wsgi_server: t.Optional[str] = None,
        wsgi_config: t.Optional[dict] = None,
        app_config: t.Optional[dict] = None,
        debug: bool = False,
    ):
        """

        :param config: app and wsgi configuration file
        :param log_config: log configuration file
        :param bind: address to bind
        :param debug: enable debug mode
        :param wsgi_class: optional a custom subclass of BaseApplication
        :param wsgi_server: wsgi server chosen
        :param wsgi_config: wsgi configuration
        :param app_config: app configuration
        :return: never returns
        """
        config_data = self.prepare_config(config, debug, bind, log_config)
        wsgi_server = wsgi_server or config_data.wsgi_server
        conf_wsgi = config_data.get("wsgi_opts") or config_data.get("wsgi") or {}
        wsgi_config = {**conf_wsgi, **(wsgi_config or {})}
        app_config = {**(config_data.get("app") or {}), **(app_config or {})}

        if wsgi_server:
            wsgi_class = self._wsgi_factory.get_class(wsgi_server)
        elif wsgi_class is None:
            wsgi_class = self._wsgi_factory.get_class("builtin")

        app = self._app_factory.create(app_config)
        wsgi = wsgi_class(app, options=wsgi_config)
        wsgi.run()  # run forever
