from flask_pymongo import PyMongo
from vbcore.datastruct import ObjectDict
from vbcore.date_helper import Seconds


class FlaskMongoDB(PyMongo):
    def init_app(self, app, *args, ext_name: str = "default", **kwargs):
        self.set_default_config(app, **kwargs)
        super().init_app(app, *args, **app.config.MONGO_OPTS)
        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["mongo"] = ObjectDict()
        app.extensions["mongo"][ext_name] = self

    @classmethod
    def set_default_config(cls, app, **kwargs):
        app.config.setdefault("MONGO_URI", "mongodb://localhost")
        app.config.setdefault("MONGO_OPTS", {})

        timeout = app.config.MONGO_OPTS.pop("timeout", None)
        default_timeout = timeout or Seconds.millis

        app.config.MONGO_OPTS.setdefault("appname", app.config.APP_NAME)
        app.config.MONGO_OPTS.setdefault("directConnection", False)
        app.config.MONGO_OPTS.setdefault("minPoolSize", 0)
        app.config.MONGO_OPTS.setdefault("maxPoolSize", 100)
        app.config.MONGO_OPTS.setdefault("maxConnecting", 2)
        app.config.MONGO_OPTS.setdefault("retryWrites", True)
        app.config.MONGO_OPTS.setdefault("retryReads", True)
        app.config.MONGO_OPTS.setdefault("maxIdleTimeMS", None)
        app.config.MONGO_OPTS.setdefault("waitQueueTimeoutMS", None)
        app.config.MONGO_OPTS.setdefault("document_class", ObjectDict)
        app.config.MONGO_OPTS.setdefault("socketTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("connectTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("serverSelectionTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("heartbeatFrequencyMS", Seconds.millis * 10)

        app.config.MONGO_OPTS.update(**kwargs)
