from multiprocessing import cpu_count

try:
    from waitress import serve
except ImportError:
    serve = None  # type: ignore

from .base import BaseApplication


class WSGIWaitress(BaseApplication):
    def run(self):
        """

        :return:
        """
        self.options.setdefault("threads", cpu_count())
        assert serve is not None, "You must install 'waitress'"

        serve(
            self.application,
            host=self._interface,
            port=self._port,
            threads=self.options["threads"],
        )
