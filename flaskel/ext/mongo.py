try:
    from flask_pymongo import PyMongo
except (ModuleNotFoundError, ImportError):
    PyMongo = object

from flaskel import ObjectDict


class FlaskMongoDB(PyMongo):
    def init_app(self, app, uri=None, ext_name='default', *args, **kwargs):
        """

        :param app:
        :param uri:
        :param ext_name:
        :param args:
        :param kwargs:
        """
        assert PyMongo is not object

        app.config.setdefault('MONGO_OPTS', {})
        app.config['MONGO_OPTS'].update(**kwargs)

        super().init_app(app, uri, *args, **kwargs)
        app.extensions['mongo'] = ObjectDict()
        app.extensions['mongo'][ext_name] = self
