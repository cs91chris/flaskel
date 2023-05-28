import atexit

# noinspection PyUnresolvedReferences
from logging.config import ConvertingDict, ConvertingList, valid_ident  # type: ignore
from logging.handlers import (
    QueueHandler as BaseQueueHandler,
    QueueListener,
    SysLogHandler,
)
from queue import Queue

from flask import _request_ctx_stack, current_app as cap


class FlaskSysLogHandler(SysLogHandler):
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        super().__init__(**kwargs)
        self.facility = kwargs.get("facility") or SysLogHandler.LOG_USER
        self._app_name = cap.config["LOG_APP_NAME"]

    def emit(self, record):
        """

        :param record:
        """
        priority = self.encodePriority(
            self.facility, self.mapPriority(record.levelname)
        )
        record.ident = f"{self._app_name}[{priority}]:"
        super().emit(record)


class QueueHandler(BaseQueueHandler):
    """From: https://rob-blackbourn.medium.com/how-to-use-python-logging-queuehandler-with-dictconfig-1e8b1284e27a"""  # noqa: E501

    def __init__(
        self,
        handlers,
        respect_handler_level=False,
        auto_run=True,
        stop_wait=False,
        queue=None,
    ):
        # noinspection PyTypeChecker
        queue = self._resolve_queue(queue or Queue(-1))
        super().__init__(queue)
        handlers = self._resolve_handlers(handlers)
        # noinspection PyUnresolvedReferences
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
        if top:
            return top.request

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

    def emit(self, record):
        return super().emit(record)

    @staticmethod
    def _resolve_handlers(h):
        if not isinstance(h, ConvertingList):
            return h
        return [h[i] for i in range(len(h))]

    @staticmethod
    def _resolve_queue(q):
        if not isinstance(q, ConvertingDict):
            return q
        if "__resolved_value__" in q:
            return q["__resolved_value__"]

        cname = q.pop("class")
        klass = q.configurator.resolve(cname)
        props = q.pop(".", None) or {}
        kwargs = {k: q[k] for k in q if valid_ident(k)}
        result = klass(**kwargs)
        for name, value in props.items():
            setattr(result, name, value)

        q["__resolved_value__"] = result
        return result
