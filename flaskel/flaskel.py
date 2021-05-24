import flask
from flask import current_app as cap
from flask_response_builder import encoders
from werkzeug.utils import safe_join

from .http import httpcode
from .utils.datastruct import ObjectDict


class Request(flask.Request):
    @property
    def id(self):
        hdr = cap.config.REQUEST_ID_HEADER
        if hasattr(flask.g, 'request_id'):
            return flask.g.request_id
        elif hdr in flask.request.headers:
            return flask.request.headers[hdr]

        flask_header_name = f"HTTP_{hdr.upper().replace('-', '_')}"
        return flask.request.environ.get(flask_header_name)

    def get_json(self, allow_empty=False, **kwargs):
        """

        :param allow_empty:
        :param kwargs:
        :return:
        """
        payload = super().get_json()
        if payload is None:
            if not allow_empty:
                flask.abort(httpcode.BAD_REQUEST, 'No JSON in request')
            payload = ObjectDict()  # pragma: no cover

        return ObjectDict.normalize(payload)


class Response(flask.Response):
    @staticmethod
    def no_content(status=httpcode.NO_CONTENT, headers=None):
        """

        :param status:
        :param headers:
        :return:
        """
        response = flask.make_response(bytes())
        response.headers.update(headers or {})
        response.headers.pop('Content-Type')
        response.headers.pop('Content-Length')
        response.status_code = status
        return response

    @staticmethod
    def send_file(directory, filename, **kwargs):
        """

        :param directory:
        :param filename:
        :param kwargs:
        """
        kwargs.setdefault('as_attachment', True)
        file_path = safe_join(directory, filename)

        try:
            resp = flask.send_file(file_path, **kwargs)
        except IOError as exc:
            cap.logger.warning(str(exc))
            flask.abort(httpcode.NOT_FOUND)
            return  # only to prevent warning # pragma: no cover

        # following headers works with nginx compatible proxy
        if cap.use_x_sendfile is True and cap.config.ENABLE_ACCEL is True:
            resp.headers['X-Accel-Redirect'] = file_path
            resp.headers['X-Accel-Charset'] = cap.config.ACCEL_CHARSET or 'utf-8'
            resp.headers['X-Accel-Buffering'] = 'yes' if cap.config.ACCEL_BUFFERING else 'no'
            if cap.config.ACCEL_LIMIT_RATE:
                resp.headers['X-Accel-Limit-Rate'] = cap.config.ACCEL_LIMIT_RATE
            if cap.config.SEND_FILE_MAX_AGE_DEFAULT:
                resp.headers['X-Accel-Expires'] = cap.config.SEND_FILE_MAX_AGE_DEFAULT

        return resp

    def get_json(self, **kwargs):
        return ObjectDict.normalize(super().get_json())


class Flaskel(flask.Flask):
    request_class = Request
    response_class = Response
    json_encoder = encoders.JsonEncoder

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = None
