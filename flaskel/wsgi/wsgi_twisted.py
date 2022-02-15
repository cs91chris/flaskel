from twisted.internet import reactor  # pylint: disable=import-error
from twisted.web.server import Site  # pylint: disable=import-error
from twisted.web.wsgi import WSGIResource  # pylint: disable=import-error

from .base import BaseApplication


class WSGITwisted(BaseApplication):
    def __init__(self, app, options=None):
        BaseApplication.__init__(self, app, options)
        # noinspection PyUnresolvedReferences
        # pylint: disable=no-member
        resource = WSGIResource(reactor, reactor.getThreadPool(), self.application)
        self.site = Site(resource)

    def run(self):
        # noinspection PyUnresolvedReferences
        # pylint: disable=no-member
        reactor.listenTCP(self._port, self.site, interface=self._interface)
        # noinspection PyUnresolvedReferences
        reactor.run()  # pylint: disable=no-member
