import os.path
import typing as t

import flask
from vbcore.datastruct import Dumper, ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum
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
    def id(self) -> t.Optional[str]:  # pylint: disable=invalid-name
        hdr = cap.config.REQUEST_ID_HEADER
        if hasattr(flask.g, "request_id"):
            return flask.g.request_id
        if hdr in flask.request.headers:
            return flask.request.headers[hdr]

        if not hdr:
            return None

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
        response.headers.pop(HeaderEnum.CONTENT_TYPE)
        response.headers.pop(HeaderEnum.CONTENT_LENGTH)
        response.status_code = status
        return t.cast("Response", response)

    @classmethod
    def set_sendfile_headers(cls, response: "Response", file_path: str) -> "Response":
        hdr = HeaderEnum
        conf = cap.config
        response.headers[hdr.X_ACCEL_REDIRECT] = os.path.abspath(file_path)
        response.headers[hdr.X_ACCEL_CHARSET] = conf.ACCEL_CHARSET or "utf-8"
        response.headers[hdr.X_ACCEL_BUFFERING] = (
            "yes" if conf.ACCEL_BUFFERING else "no"
        )
        if conf.ACCEL_LIMIT_RATE:
            response.headers[hdr.X_ACCEL_LIMIT_RATE] = conf.ACCEL_LIMIT_RATE
        if conf.SEND_FILE_MAX_AGE_DEFAULT:
            response.headers[hdr.X_ACCEL_EXPIRES] = conf.SEND_FILE_MAX_AGE_DEFAULT
        return response

    @classmethod
    def send_file(cls, directory: str, filename: str, **kwargs) -> "Response":
        kwargs.setdefault("as_attachment", True)
        file_path = safe_join(directory, filename)

        try:
            response = flask.send_file(file_path, etag=True, conditional=True, **kwargs)
        except IOError as exc:
            cap.logger.warning(str(exc))
            return flask.abort(httpcode.NOT_FOUND)

        if cap.use_x_sendfile is True and cap.config.ENABLE_ACCEL is True:
            # following headers works with nginx compatible proxy
            return cls.set_sendfile_headers(response, file_path)
        return response

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
