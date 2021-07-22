from .base import WSGIBuiltin

try:
    from .gevent import WSGIGevent
except ImportError:
    WSGIGevent = None  # type: ignore
try:
    from .gunicorn import WSGIGunicorn
except ImportError:
    WSGIGunicorn = None  # type: ignore
try:
    from .tornado import WSGITornado
except ImportError:
    WSGITornado = None  # type: ignore
try:
    from .twisted import WSGITwisted
except ImportError:
    WSGITwisted = None  # type: ignore
try:
    from .waitress import WSGIWaitress
except ImportError:
    WSGIWaitress = None  # type: ignore


class WSGIFactory:
    WSGI_SERVERS = {
        "builtin": WSGIBuiltin,
        "gunicorn": WSGIGunicorn,
        "gevent": WSGIGevent,
        "tornado": WSGITornado,
        "twisted": WSGITwisted,
        "waitress": WSGIWaitress,
    }

    @classmethod
    def get_instance(cls, name, **kwargs):
        """

        :param name:
        :param kwargs:
        :return:
        """
        wsgi_class = cls.get_class(name)
        return wsgi_class(**kwargs)

    @classmethod
    def get_class(cls, name):
        """

        :param name:
        :return:
        """
        if name not in cls.WSGI_SERVERS:
            raise ValueError("unable to find wsgi server: '{}'".format(name))

        wsgi_class = cls.WSGI_SERVERS.get(name)

        if wsgi_class is None:
            raise ImportError("You must install '{}' dependencies".format(name))

        return wsgi_class
