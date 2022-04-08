import typing as t

from tornado.httpserver import HTTPServer  # pylint: disable=import-error
from tornado.ioloop import IOLoop  # pylint: disable=import-error
from tornado.wsgi import WSGIContainer  # pylint: disable=import-error

from flaskel import Flaskel

from .base import BaseApplication


class WSGITornado(BaseApplication):
    def __init__(self, app: Flaskel, options: t.Optional[dict] = None):
        BaseApplication.__init__(self, app, options)
        self.http_server = HTTPServer(WSGIContainer(self.application))

    def run(self):
        self.http_server.listen(address=self._interface, port=self._port)
        IOLoop.current().start()
