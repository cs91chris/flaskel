import typing as t

from flaskel import Flaskel


class BaseApplication:
    default_host = "127.0.0.1"
    default_port = 5000

    def __init__(self, app: Flaskel, options: t.Optional[dict] = None):
        self.application = app
        self.options = options or {}

        default_bind = f"{self.default_host}:{self.default_port}"
        bind = (self.options.get("bind") or default_bind).split(":")

        self._interface = bind[0] or self.default_host
        self._port = int(bind[1]) if len(bind) > 1 else self.default_port
        self._bind = (self._interface, self._port)

    def run(self):
        raise NotImplementedError  # pragma: no cover


class WSGIBuiltin(BaseApplication):
    def run(self):
        debug = self.application.config.DEBUG or False
        self.application.run(host=self._interface, port=self._port, debug=debug)
