try:
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    from tornado.wsgi import WSGIContainer
except ImportError:
    HTTPServer = IOLoop = WSGIContainer = object

from .base import BaseApplication


class WSGITornado(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        assert HTTPServer is not object, "you must install 'tornado'"
        BaseApplication.__init__(self, app, options)
        self._http_server = HTTPServer(WSGIContainer(self.application))

    def run(self):
        self._http_server.listen(address=self._interface, port=self._port)
        IOLoop.current().start()
