import functools
import inspect
import typing as t

import flask

from flaskel import HttpMethod
from flaskel.ext.default import builder
from flaskel.flaskel import Response
from flaskel.flaskel import cap
from flaskel.flaskel import httpcode
from flaskel.http import rpc
from flaskel.utils.batch import BatchExecutor
from flaskel.utils.datastruct import ObjectDict
from .base import BaseView

RPCPayloadType = t.Union[t.List[dict], dict]
OperationsType = t.Dict[t.Optional[str], t.Dict[str, t.Callable]]


class JSONRPCView(BaseView):
    version = "2.0"
    separator = "."
    operations: OperationsType = {}

    default_view_name = "jsonrpc"
    default_urls = ("/jsonrpc",)

    methods = [
        HttpMethod.POST,
    ]
    decorators = [
        builder.response("json"),
    ]

    def __init__(
        self,
        operations: OperationsType = None,
        batch_executor: t.Type[BatchExecutor] = BatchExecutor,
        **kwargs,
    ):
        """

        :param batch_executor
        :param operations: a dict of jsonrpc operations like:
            {
                None: {
                    "action1": funct1,
                    "action2": funct2,
                    ...
                },
                "method1": {
                    "action1": funct1,
                    "action2": funct2,
                    ...
                },
                ...
            }
        """
        self.operations = operations or {}
        self._batch_executor = batch_executor
        self._batch_args = kwargs

    def _validate_request(self, data: dict):
        if "jsonrpc" not in data or "method" not in data:
            raise rpc.RPCInvalidRequest() from None

        if data["jsonrpc"] != self.version:
            raise rpc.RPCInvalidRequest(
                f"jsonrpc version is {self.version}", req_id=data.get("id")
            ) from None

    def _validate_payload(self) -> RPCPayloadType:
        payload: RPCPayloadType = flask.request.get_json(True)
        if not payload:
            raise rpc.RPCParseError() from None

        if isinstance(payload, (list, tuple)):
            max_requests = cap.config.JSONRPC_BATCH_MAX_REQUEST  # type: ignore
            if max_requests and len(payload) > max_requests:
                mess = f"Operations in a single http request must be less than {max_requests}"
                flask.abort(httpcode.REQUEST_ENTITY_TOO_LARGE, mess)
            for d in payload:
                self._validate_request(d)
        else:
            self._validate_request(payload)

        return payload

    def _get_action(self, method: str):
        """

        :param method:
        :return:
        """
        m = method.split(self.separator)
        if len(m) > 1:
            op, action = m[0], self.separator.join(m[1:])
        else:
            op, action = None, m[0]

        try:
            return self.operations[op][action]
        except (IndexError, TypeError, KeyError) as exc:
            cap.logger.debug(exc)
            raise rpc.RPCMethodNotFound()

    def dispatch_request(self, *_, **__):
        """

        :return:
        """
        tasks = []
        responses = []

        try:
            payload = self._validate_payload()
        except rpc.RPCError as ex:
            return (
                ObjectDict(
                    jsonrpc=self.version,
                    id=getattr(ex, "req_id", None),
                    error=ex.as_dict(),
                ),
                httpcode.BAD_REQUEST,
            )

        for d in payload if isinstance(payload, list) else [payload]:
            resp = ObjectDict(jsonrpc=self.version, id=None)
            try:
                if "id" not in d:
                    tasks.append(
                        (self._get_action(d["method"]), {**(d.get("params") or {})})
                    )
                else:
                    resp.id = d.get("id")  # pylint: disable=invalid-name
                    action = self._get_action(d["method"])
                    resp.result = action(**(d.get("params") or {}))
            except rpc.RPCError as ex:
                resp.error = ex.as_dict()
            except Exception as ex:  # pylint: disable=W0703
                cap.logger.exception(ex)
                mess = str(ex) if cap.debug is True else None
                resp.error = rpc.RPCInternalError(message=mess).as_dict()

            if "id" in d:
                responses.append(resp)

        self._batch_executor(tasks=tasks, **self._batch_args).run()

        if not responses:
            res = Response.no_content()
            return None, res.status_code, res.headers

        if isinstance(payload, (list, tuple)):
            if len(responses) > 1:
                return responses, httpcode.MULTI_STATUS
            return responses

        return responses[0]

    @classmethod
    def load_from_object(cls, obj):
        """

        :param obj:
        """
        for name, member in inspect.getmembers(obj, predicate=inspect.isroutine):
            if not name.startswith("_"):
                cls.method(obj.__class__.__name__, name)(member)

    @classmethod
    def method(cls, name=None, operation=None):  # pylint: disable=W0613
        """

        :param name:
        :param operation:
        :return:
        """

        def _method(func):
            nonlocal name
            name = name or func.__name__

            @functools.wraps(func)
            def wrapped():
                obj = {operation: func}
                if name not in cls.operations:
                    cls.operations[name] = obj
                else:
                    cls.operations[name].update(obj)

            return wrapped()

        return _method

    @classmethod
    def register(cls, app, name=None, urls=(), **kwargs):
        kwargs.setdefault("operations", cls.operations)
        return super().register(app, name, urls, **kwargs)
