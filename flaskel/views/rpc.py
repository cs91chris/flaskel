import functools
import inspect
import typing as t

from vbcore.batch import BatchExecutor
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod, rpc

from flaskel import abort, cap, request, Response
from flaskel.ext.default import builder

from .base import BaseView, UrlsType

# {
#     None: {
#         "action1": funct1,
#         "action2": funct2,
#         ...
#     },
#     "method1": {
#         "action1": funct1,
#         "action2": funct2,
#         ...
#     },
#     ...
# }
OperationsType = t.Dict[t.Optional[str], t.Dict[str, t.Callable]]
RPCPayloadType = t.Union[t.List[dict], dict]


class JSONRPCView(BaseView):
    version: str = "2.0"
    separator: str = "."
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

    def _validate_payload(self) -> t.Tuple[t.List[dict], bool]:
        payload: RPCPayloadType = request.get_json(True)
        if not payload:
            raise rpc.RPCParseError() from None

        if isinstance(payload, (list, tuple)):
            max_requests = cap.config.JSONRPC_BATCH_MAX_REQUEST  # type: ignore
            if max_requests and len(payload) > max_requests:
                mess = f"Operations in a single http request must be less than {max_requests}"
                abort(httpcode.REQUEST_ENTITY_TOO_LARGE, mess)
            for d in payload:
                self._validate_request(d)
        else:
            self._validate_request(payload)

        return (payload, True) if isinstance(payload, list) else ([payload], False)

    def _get_action(self, method: str) -> t.Callable:
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
        tasks = []
        responses = []

        try:
            payload, is_batch = self._validate_payload()
        except rpc.RPCError as ex:
            return (
                ObjectDict(
                    jsonrpc=self.version,
                    id=getattr(ex, "req_id", None),
                    error=ex.as_dict(),
                ),
                httpcode.BAD_REQUEST,
            )

        for d in payload:
            resp = ObjectDict(jsonrpc=self.version, id=None)
            try:
                params = d.get("params") or {}
                if "id" not in d:
                    tasks.append((self._get_action(d["method"]), params))
                else:
                    resp.id = d.get("id")
                    action = self._get_action(d["method"])
                    resp.result = action(**params)
            except rpc.RPCError as exc:
                cap.logger.exception(exc)
                resp.error = exc.as_dict()
            except Exception as exc:  # pylint: disable=broad-except
                cap.logger.exception(exc)
                mess = str(exc) if cap.debug is True else None
                resp.error = rpc.RPCInternalError(message=mess).as_dict()

            if "id" in d:
                responses.append(resp)

        self._batch_executor(tasks=tasks, **self._batch_args).run()
        return self.prepare_responses(responses, is_batch)

    @classmethod
    def prepare_responses(cls, responses: t.List[dict], is_batch: bool):
        if not responses:
            res = Response.no_content()
            return None, res.status_code, res.headers

        if is_batch:
            if len(responses) > 1:
                return responses, httpcode.MULTI_STATUS
            return responses

        return responses[0]

    @classmethod
    def load_from_object(cls, obj):
        for name, member in inspect.getmembers(obj, predicate=inspect.isroutine):
            if not name.startswith("_"):
                cls.method(obj.__class__.__name__, name)(member)

    @classmethod
    def method(cls, name: t.Optional[str] = None, operation: t.Optional[str] = None):
        def _method(func):
            _name = name or func.__name__

            @functools.wraps(func)
            def wrapped():
                obj = {operation: func}
                if _name not in cls.operations:
                    cls.operations[_name] = obj
                else:
                    cls.operations[_name].update(obj)

            return wrapped()

        return _method

    @classmethod
    def register(
        cls,
        app,
        name: t.Optional[str] = None,
        urls: UrlsType = (),
        view: t.Optional[t.Type[BaseView]] = None,
        **kwargs,
    ) -> t.Callable:
        kwargs.setdefault("operations", cls.operations)
        return super().register(app, name, urls, view, **kwargs)
