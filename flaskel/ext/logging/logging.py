import logging
import logging.config
from functools import wraps

import flask
import yaml

from .builders import builder_factory, LogBuilder


class FlaskLogging:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        """
        self._conf = {}

        if app is not None:
            self.init_app(app, **kwargs)

    @property
    def conf(self):
        """

        :return:
        """
        return self._conf

    def init_app(self, app, builder=None):
        """

        :param app: Flask app instance
        :param builder:
        """
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["logify"] = self

        self.set_default_config(app)
        self.set_request_id(app)

        if app.config["LOG_BUILDER"]:
            builder = builder_factory(app.config["LOG_BUILDER"])

        if isinstance(builder, str):
            builder = builder_factory(builder)

        if builder:
            assert isinstance(builder, LogBuilder)
            app.before_request_funcs.setdefault(None, []).append(builder.dump_request)
            app.after_request_funcs.setdefault(None, []).append(builder.dump_response)

        if app.config["LOG_FILE_CONF"]:
            try:
                with open(app.config["LOG_FILE_CONF"], encoding="utf-8") as f:
                    self._conf = yaml.safe_load(f)
            except (OSError, IOError, yaml.YAMLError) as exc:
                app.logger.exception(exc, stack_info=False)

        if not self._conf and app.config["LOGGING"]:
            self._conf = app.config["LOGGING"]

        if self._conf:
            try:
                logging.config.dictConfig(self._conf)
                app.logger = logging.getLogger(app.config["LOG_LOGGER_NAME"])
            except ValueError as exc:
                app.logger.error(
                    "bad configuration file: %s", app.config["LOG_FILE_CONF"]
                )
                app.logger.error("the configuration below\n", self._conf)
                app.logger.exception(exc, stack_info=False)
        else:
            app.logger.warning(
                "No logging configuration provided using default configuration"
            )

    @staticmethod
    def set_request_id(app):
        """
        Register request id in flask g

        param app: Flask app instance
        """

        @app.before_request
        def req_id():
            h = flask.current_app.config["REQUEST_ID_HEADER"]
            header = f"HTTP_{h.upper().replace('-', '_')}"
            flask.g.request_id = flask.request.environ.get(header)

    @staticmethod
    def disabled(filter_class, loggers=None, **options):
        """
        Disable log messages for log handler for a specific Flask routes

        :param (class) filter_class: subclass of logging.Filter
        :param (list) loggers: logger name's list
        :param (str) options: passed to filter class constructor
        :return: wrapped function
        """
        if not issubclass(filter_class, logging.Filter):
            name = logging.Filter.__name__
            raise ValueError(f"'{filter_class}' must be subclass of {name}")

        if not loggers:
            loggers = [None]  # root logger has no name
            # noinspection PyUnresolvedReferences
            loggers += list(logging.root.manager.loggerDict.keys())

        def response(fun):
            for log in loggers:
                logger = logging.getLogger(log or "")
                logger.addFilter(filter_class(**options))

            @wraps(fun)
            def wrapper(*args, **kwargs):
                return fun(*args, **kwargs)

            return wrapper

        return response

    @staticmethod
    def set_default_config(app):
        """

        param app: Flask app instance
        """
        app.config.setdefault("LOGGING", None)
        app.config.setdefault("LOG_FILE_CONF", None)
        app.config.setdefault("LOG_BUILDER", "text")
        app.config.setdefault("REQUEST_ID_HEADER", "X-Request-ID")

        app.config.setdefault("LOG_REQ_SKIP_DUMP", not app.debug)
        app.config.setdefault("LOG_REQ_HEADERS", [])
        app.config.setdefault(
            "LOG_REQ_FORMAT",
            "INCOMING REQUEST: {address} {method} {scheme} {path}{headers}{body}",
        )

        app.config.setdefault("LOG_RESP_SKIP_DUMP", app.debug)
        app.config.setdefault("LOG_RESP_HEADERS", [])
        app.config.setdefault(
            "LOG_RESP_FORMAT",
            "OUTGOING RESPONSE for {address} at {path}: {level} STATUS {status}{headers}{body}",
        )

        env = app.config.get("FLASK_ENV") or "development"
        app.config.setdefault("LOG_APP_NAME", app.config.get("APP_NAME") or "flask")
        app.config.setdefault("LOG_LOGGER_NAME", f"{env}")
