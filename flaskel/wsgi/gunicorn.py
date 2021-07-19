try:
    from gunicorn.app.base import BaseApplication as WSGIServer
except ImportError:
    WSGIServer = object

from .base import BaseApplication


class WSGIGunicorn(BaseApplication, WSGIServer):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        assert WSGIServer is not object, "you must install 'gunicorn'"
        BaseApplication.__init__(self, app, options)
        WSGIServer.__init__(self)

    def load_config(self):
        options = {}

        for k, v in self.options.items():
            if k in self.cfg.settings and v is not None:
                options.update({k: v})

        for key, value in options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """

        :return:
        """
        return self.application

    def init(self, parser, opts, args):
        """

        :param parser:
        :param opts:
        :param args:
        """
        # abstract in superclass

    def run(self):
        WSGIServer.run(self)
