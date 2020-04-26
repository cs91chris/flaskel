try:
    from tornado.ioloop import IOLoop
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
except ImportError:
    raise ImportError('tornado not installed') from None

from .base import BaseApplication


class WSGITornado(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        BaseApplication.__init__(self, app, options)
        self._http_server = HTTPServer(WSGIContainer(self.application))

    def run(self):
        """

        """
        self._http_server.listen()
        IOLoop.instance().start()
