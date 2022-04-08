import typing as t

from gevent.pywsgi import WSGIServer  # pylint: disable=import-error

from flaskel import Flaskel

from .base import BaseApplication


class WSGIGevent(BaseApplication, WSGIServer):
    def __init__(self, app: Flaskel, options: t.Optional[dict] = None):
        BaseApplication.__init__(self, app, options)
        WSGIServer.__init__(
            self,
            self._bind,
            self.application,
            spawn=options.get("spawn") or "default",
            backlog=options.get("backlog"),
        )

    def run(self):
        self.serve_forever()
