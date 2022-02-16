from vbcore.datastruct import ObjectDict
from vbcore.date_helper import Seconds

try:
    from flask_pymongo import PyMongo
except ImportError:
    PyMongo = object


class FlaskMongoDB(PyMongo):
    def init_app(self, app, *args, uri=None, ext_name="default", **kwargs):
        assert PyMongo is not object, "you must install 'flask_pymongo'"

        app.config.setdefault("MONGO_URI", "mongodb://localhost")
        app.config.setdefault("MONGO_OPTS", {})
        app.config["MONGO_OPTS"].setdefault("connectTimeoutMS", Seconds.millis)
        app.config["MONGO_OPTS"].setdefault("serverSelectionTimeoutMS", Seconds.millis)
        app.config["MONGO_OPTS"].update(**kwargs)

        # noinspection PyUnresolvedReferences
        super().init_app(app, uri, *args, **kwargs)
        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["mongo"] = ObjectDict()
        app.extensions["mongo"][ext_name] = self
