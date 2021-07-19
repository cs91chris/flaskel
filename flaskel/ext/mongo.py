try:
    from flask_pymongo import PyMongo
except (ModuleNotFoundError, ImportError):
    PyMongo = object

from flaskel import ObjectDict


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

        app.config.setdefault("MONGO_OPTS", {})
        app.config["MONGO_OPTS"].setdefault("connectTimeoutMS", 1000)
        app.config["MONGO_OPTS"].setdefault("serverSelectionTimeoutMS", 1000)
        app.config["MONGO_OPTS"].update(**kwargs)

        # noinspection PyUnresolvedReferences
        super().init_app(app, uri, *args, **kwargs)
        app.extensions["mongo"] = ObjectDict()
        app.extensions["mongo"][ext_name] = self
