import logging

import flask


class RequestFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        """

        :param kwargs:
        """
        self.app_name = flask.current_app.config["LOG_APP_NAME"]
        req_id_header = kwargs.pop("request_id_header", None) or "X-Request-ID"
        req_id_header = req_id_header.upper().replace("-", "_")
        self.request_id_header = f"HTTP_{req_id_header}"
        super().__init__(*args, **kwargs)

    def format(self, record):
        """

        :param record:
        :return:
        """
        record.url = None
        record.method = None
        record.scheme = None
        record.path = None
        record.remote_addr = None
        record.request_id = None

        if not flask.has_request_context():
            try:
                # noinspection PyUnresolvedReferences
                request = record.request
            except AttributeError:
                request = None
        else:
            request = flask.request

        try:
            record.url = request.url
            record.method = request.method
            record.scheme = request.scheme
            record.path = request.full_path
            record.remote_addr = request.remote_addr
            record.request_id = request.environ.get(self.request_id_header)
        except (RuntimeError, AttributeError):
            pass

        record.appname = self.app_name
        return super().format(record)
