LOG_FMT = "[%(asctime)s]" \
          "[%(levelname)s]" \
          "[%(request_id)s]" \
          "[%(name)s:%(module)s.%(funcName)s:%(lineno)d]: " \
          "%(message)s"

LOGGING = dict(
    version=1,
    disable_existing_loggers=True,
    objects={
        "queue": {
            "class":   "queue.Queue",
            "maxsize": 10000
        }
    },
    formatters={
        "console": {
            "class":  "flask_logify.formatters.RequestFormatter",
            "format": LOG_FMT
        },
        "syslog":  {
            "class":  "flask_logify.formatters.RequestFormatter",
            "format": f"%(ident)s%(message)s"
        }
    },
    handlers={
        "console":      {
            "class":     "logging.StreamHandler",
            "formatter": "console",
            "stream":    "ext://sys.stderr"
        },
        "syslog":       {
            "class":     "flask_logify.handlers.FlaskSysLogHandler",
            "address":   ["localhost", 514],
            "formatter": "syslog",
            "facility":  "user"
        },
        "queueConsole": {
            "respect_handler_level": True,
            "class":                 "flask_logify.handlers.QueueHandler",
            "queue":                 "cfg://objects.queue",
            "handlers":              ["cfg://handlers.console"]
        },
        "queueSyslog":  {
            "respect_handler_level": True,
            "class":                 "flask_logify.handlers.QueueHandler",
            "queue":                 "cfg://objects.queue",
            "handlers":              ["cfg://handlers.syslog"]
        }
    },
    root={
        "level":    "WARN",
        "handlers": ["queueConsole"]
    },
    loggers={
        "development":     {
            "level":     "DEBUG",
            "propagate": False,
            "handlers":  ["queueConsole"]
        },
        "production":      {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["queueConsole"]
        },
        "flask-limiter":   {
            "level":     "DEBUG",
            "propagate": False,
            "handlers":  ["queueConsole"]
        },
        "gunicorn.error":  {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["queueSyslog"]
        },
        "gunicorn.access": {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["queueSyslog"]
        }
    }
)
