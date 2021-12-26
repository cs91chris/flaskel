REQUEST_FORMATTER = "flask_logify.formatters.RequestFormatter"


def handler(formatter, **kwargs):
    return {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stderr",
        "formatter": formatter,
        **kwargs,
    }


LOGGING = dict(
    version=1,
    disable_existing_loggers=True,
    objects={"queue": {"class": "queue.Queue", "maxsize": 10000}},
    formatters={
        "simple": {"format": "[%(asctime)s][%(levelname)s]: %(message)s"},
        "consoleDebug": {
            "class": REQUEST_FORMATTER,
            "format": "[%(asctime)s]"
            "[%(levelname)s]"
            "[%(request_id)s]"
            "[%(name)s:%(module)s.%(funcName)s:%(lineno)d]: "
            "%(message)s",
        },
        "console": {
            "class": REQUEST_FORMATTER,
            "format": "[%(asctime)s][%(levelname)s][%(request_id)s]: %(message)s",
        },
        "syslog": {
            "class": REQUEST_FORMATTER,
            "format": "%(ident)s%(message)s",
        },
        "syslogNoRequest": {"format": "%(ident)s%(message)s"},
        "json": {
            "class": REQUEST_FORMATTER,
            "format": "{"
            '"requestId":"%(request_id)s",'
            '"level":"%(levelname)s",'
            '"datetime":"%(asctime)s",'
            '"message":%(message)s'
            "}",
        },
    },
    handlers={
        "simple": handler("simple"),
        "console": handler("console"),
        "consoleDebug": handler("consoleDebug"),
        "syslog": {
            "class": "flask_logify.handlers.FlaskSysLogHandler",
            "address": ["localhost", 514],
            "formatter": "syslog",
            "facility": "user",
        },
        "syslogNoRequest": {
            "class": "flask_logify.handlers.FlaskSysLogHandler",
            "address": ["localhost", 514],
            "formatter": "syslogNoRequest",
            "facility": "user",
        },
        "queueConsole": {
            "respect_handler_level": True,
            "class": "flask_logify.handlers.QueueHandler",
            "queue": "cfg://objects.queue",
            "handlers": ["cfg://handlers.console"],
        },
        "queueSyslogNoRequest": {
            "respect_handler_level": True,
            "class": "flask_logify.handlers.QueueHandler",
            "queue": "cfg://objects.queue",
            "handlers": ["cfg://handlers.syslogNoRequest"],
        },
    },
    root={"level": "WARN", "handlers": ["simple"]},
    loggers={
        "development": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["consoleDebug"],
        },
        "developmentQueue": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["queueConsole"],
        },
        "production": {"level": "INFO", "propagate": False, "handlers": ["console"]},
        "productionQueue": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["queueConsole"],
        },
        "flask-limiter": {"level": "DEBUG", "propagate": False, "handlers": ["simple"]},
        "gunicorn.error": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["queueSyslogNoRequest"],
        },
        "gunicorn.access": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["queueSyslogNoRequest"],
        },
    },
)

if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(LOGGING))
