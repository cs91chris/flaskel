from multiprocessing import cpu_count

from waitress import serve  # pylint: disable=import-error

from .base import BaseApplication


class WSGIWaitress(BaseApplication):
    def run(self):
        self.options.setdefault("threads", cpu_count())

        serve(
            self.application,
            host=self._interface,
            port=self._port,
            threads=self.options["threads"],
        )
