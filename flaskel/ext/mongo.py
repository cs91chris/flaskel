try:
    from flask_pymongo import PyMongo
except (ModuleNotFoundError, ImportError):
    PyMongo = object

from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.datetime import Seconds


class FlaskMongoDB(PyMongo):
    def init_app(self, app, *args, uri=None, ext_name="default", **kwargs):
        """

        :param app:
        :param uri:
        :param ext_name:
        :param args:
        :param kwargs:
        """
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


mongodb = FlaskMongoDB()
