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
            "format": f"%(ident)s{LOG_FMT}"
        }
    },
    handlers={
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "console",
            "stream":    "ext://sys.stderr"
        },
        "queue":   {
            "respect_handler_level": True,
            "class":                 "flask_logify.handlers.QueueHandler",
            "queue":                 "cfg://objects.queue",
            "handlers":              ["cfg://handlers.console"]
        },
        "syslog":  {
            "class":     "flask_logify.handlers.FlaskSysLogHandler",
            "address":   ["localhost", 514],
            "formatter": "syslog",
            "facility":  "user"
        }
    },
    root={
        "level":    "WARN",
        "handlers": ["console"]
    },
    loggers={
        "development":     {
            "level":     "DEBUG",
            "propagate": False,
            "handlers":  ["console"]
        },
        "production":      {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["syslog"]
        },
        "flask-limiter":   {
            "level":     "DEBUG",
            "propagate": False,
            "handlers":  ["console"]
        },
        "gunicorn.error":  {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["console"]
        },
        "gunicorn.access": {
            "level":     "INFO",
            "propagate": False,
            "handlers":  ["console"]
        }
    }
)
