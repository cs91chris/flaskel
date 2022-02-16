import typing as t

import flask
from vbcore.datastruct import ObjectDict, Dumper
from vbcore.http import httpcode
from vbcore.json import JsonEncoder
from werkzeug.routing import Rule
from werkzeug.utils import safe_join

cap: "Flaskel" = t.cast("Flaskel", flask.current_app)
request: "Request" = t.cast("Request", flask.request)


class Config(flask.Config, ObjectDict):
    def __init__(self, root_path: str, defaults: t.Optional[dict] = None):
        flask.Config.__init__(self, root_path, defaults)
        ObjectDict.__init__(self)


class DumpUrls(Dumper):
    def __init__(self, app: flask.Flask):
        super().__init__(app.url_map.iter_rules())

    @property
    def rules(self) -> t.Iterator[Rule]:
        return self.data

    def dump(self) -> str:
        output = []
        for rule in self.rules:
            methods = ",".join(rule.methods)
            output.append(f"{rule.endpoint}:30s {methods}:40s {rule}")
        return "\n".join(sorted(output))


class Request(flask.Request):
    @property
    def id(self) -> t.Optional[str]:
        hdr = cap.config.REQUEST_ID_HEADER
        if hasattr(flask.g, "request_id"):
            return flask.g.request_id
        if hdr in flask.request.headers:
            return flask.request.headers[hdr]

        flask_header_name = f"HTTP_{hdr.upper().replace('-', '_')}"
        return flask.request.environ.get(flask_header_name)

    def get_json(self, *args, allow_empty=False, **kwargs) -> ObjectDict:
        """

        :param allow_empty:
        :return:
        """
        payload = super().get_json(*args, **kwargs)
        if payload is None:
            if not allow_empty:
                flask.abort(httpcode.BAD_REQUEST, "No JSON in request")
            payload = ObjectDict()  # pragma: no cover

        return ObjectDict.normalize(payload)


class Response(flask.Response):
    @classmethod
    def no_content(cls, status=httpcode.NO_CONTENT, headers=None) -> "Response":
        """

        :param status:
        :param headers:
        :return:
        """
        response = flask.make_response(bytes())
        response.headers.update(headers or {})
        response.headers.pop("Content-Type")
        response.headers.pop("Content-Length")
        response.status_code = status
        return t.cast("Response", response)

    @classmethod
    def send_file(cls, directory, filename, **kwargs) -> "Response":
        """

        :param directory:
        :param filename:
        :param kwargs:
        """
        kwargs.setdefault("as_attachment", True)
        file_path = safe_join(directory, filename)

        try:
            resp = flask.send_file(file_path, **kwargs)
        except IOError as exc:
            cap.logger.warning(str(exc))
            return flask.abort(httpcode.NOT_FOUND)

        # following headers works with nginx compatible proxy
        if cap.use_x_sendfile is True and cap.config.ENABLE_ACCEL is True:
            resp.headers["X-Accel-Redirect"] = file_path
            resp.headers["X-Accel-Charset"] = cap.config.ACCEL_CHARSET or "utf-8"
            resp.headers["X-Accel-Buffering"] = (
                "yes" if cap.config.ACCEL_BUFFERING else "no"
            )
            if cap.config.ACCEL_LIMIT_RATE:
                resp.headers["X-Accel-Limit-Rate"] = cap.config.ACCEL_LIMIT_RATE
            if cap.config.SEND_FILE_MAX_AGE_DEFAULT:
                resp.headers["X-Accel-Expires"] = cap.config.SEND_FILE_MAX_AGE_DEFAULT

        return resp

    def get_json(self, *args, **kwargs) -> ObjectDict:
        return ObjectDict.normalize(super().get_json(*args, **kwargs))


class Flaskel(flask.Flask):
    config_class = Config
    request_class = Request
    response_class = Response
    json_encoder = JsonEncoder

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = None
        self.config: Config
