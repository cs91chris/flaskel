import atexit
from logging.handlers import (
    QueueHandler as BaseQueueHandler,
    QueueListener,
    SysLogHandler,
)
from queue import Queue

from flask import _request_ctx_stack, current_app as cap


class FlaskSysLogHandler(SysLogHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.facility = kwargs.get("facility") or SysLogHandler.LOG_USER
        self._app_name = cap.config["LOG_APP_NAME"]

    def emit(self, record):
        priority = self.encodePriority(
            self.facility, self.mapPriority(record.levelname)
        )
        record.ident = f"{self._app_name}[{priority}]:"
        super().emit(record)


class QueueHandler(BaseQueueHandler):
    def __init__(
        self,
        handlers,
        respect_handler_level=False,
        auto_run=True,
        stop_wait=False,
        queue=None,
    ):
        super().__init__(queue or Queue(-1))
        self._listener = QueueListener(
            self.queue, *handlers, respect_handler_level=respect_handler_level
        )
        if auto_run is True:
            self.start()
            if stop_wait is True:
                atexit.register(self.stop)

    @staticmethod
    def _get_request_context():
        """
        Return the current request context which can then be used in queued handler
        """
        top = _request_ctx_stack.top
        return top.request if top else None

    def prepare(self, record):
        """
        Return a prepared log record.
        Attach a request context for use inside threaded handlers
        """
        record = super().prepare(record)
        record.request = self._get_request_context()
        return record

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()
