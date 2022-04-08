import typing as t

from vbcore.importer import ImporterError, ImporterFactory

from .base import BaseApplication

DEFAULT_WSGI_SERVERS: t.Dict[str, str] = {
    "builtin": "flaskel.wsgi.base:WSGIBuiltin",
    "gunicorn": "flaskel.wsgi.wsgi_gunicorn:WSGIGunicorn",
    "gevent": "flaskel.wsgi.wsgi_gevent:WSGIGevent",
    "tornado": "flaskel.wsgi.wsgi_tornado.WSGITornado",
    "twisted": "flaskel.wsgi.wsgi_twisted:WSGITwisted",
    "waitress": "flaskel.wsgi.wsgi_waitress:WSGIWaitress",
}


class WSGIFactory(ImporterFactory):
    def get_class(self, name: str, *args, **kwargs) -> t.Type[BaseApplication]:
        try:
            return super().get_class(name, *args, **kwargs)
        except ImporterError as exc:
            raise ImportError(f"missing '{name}' dependency") from exc
