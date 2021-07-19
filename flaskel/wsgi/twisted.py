try:
    from twisted.internet import reactor
    from twisted.web.server import Site
    from twisted.web.wsgi import WSGIResource
except ImportError:
    reactor = None
    Site = WSGIResource = object

from .base import BaseApplication


class WSGITwisted(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        assert WSGIResource is not object, "you must install 'twisted'"
        BaseApplication.__init__(self, app, options)
        resource = WSGIResource(reactor, reactor.getThreadPool(), self.application)
        self._site = Site(resource)

    def run(self):
        reactor.listenTCP(self._port, self._site, interface=self._interface)
        reactor.run()
