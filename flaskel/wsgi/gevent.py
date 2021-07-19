try:
    from gevent.pywsgi import WSGIServer
except ImportError:
    WSGIServer = object

from .base import BaseApplication


class WSGIGevent(BaseApplication, WSGIServer):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        assert WSGIServer is not object, "you must install 'gevent'"
        BaseApplication.__init__(self, app, options)
        opts = dict(
            spawn=options.get("spawn") or "default", backlog=options.get("backlog")
        )
        WSGIServer.__init__(self, self._bind, self.application, **opts)

    def run(self):
        self.serve_forever()
