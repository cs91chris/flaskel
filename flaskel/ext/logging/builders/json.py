from abc import ABC
from datetime import datetime

import flask
from flask import current_app as cap

from .base import BaseWrapper, LogBuilder


class Wrapper(BaseWrapper, ABC):
    @staticmethod
    def package_message(identifier, payload):
        """

        :param identifier:
        :param payload:
        :return:
        """
        return flask.json.dumps(
            {
                "appName": cap.config["LOG_APP_NAME"],
                "serverName": cap.config["SERVER_NAME"],
                "timestamp": datetime.utcnow().timestamp(),
                "type": identifier,
                **payload,
            },
            separators=(",", ":"),
        )

    @staticmethod
    def dump_headers(hdr, only=()):
        """
        dumps http headers

        :param hdr: headers' dictionary
        :param only: list of headers key to dump
        :return: string representation of headers
                k1: v1
                k2: v2
        """

        def dump(h):
            return dict(h.items())

        if only:
            return dump({k: hdr[k] for k in only if k in hdr})

        return dump(hdr)

    @staticmethod
    def dump_body(r):
        """

        :param r:
        :return:
        """
        body = r.get_json()
        if body:
            return body

        try:
            return r.get_data(as_text=True)
        except UnicodeError:
            return "body not dumped: invalid encoding or binary"


class RequestWrap(Wrapper):
    def dump(self):
        request = self.data
        skip = self.opts.get("skip")
        hdr = self.opts.get("only")
        address = self.opts.get("address")

        return self.package_message(
            "request",
            {
                "address": address,
                "method": request.method,
                "scheme": request.scheme,
                "path": request.full_path,
                "headers": self.dump_headers(request.headers, hdr)
                if hdr or not skip
                else "",
                "body": self.dump_body(request) if not skip else "",
            },
        )


class ResponseWrap(Wrapper):
    def dump(self):
        response = self.data
        skip = self.opts.get("skip")
        hdr = self.opts.get("only")

        return self.package_message(
            "response",
            {
                "path": flask.request.path,
                "status": response.status_code,
                "headers": self.dump_headers(response.headers, hdr)
                if hdr or not skip
                else "",
                "body": self.dump_body(response) if not skip else "",
            },
        )


class LogJSONBuilder(LogBuilder):
    wrapper_dump_request = RequestWrap
    wrapper_dump_response = ResponseWrap

    def request_params(self):
        return {
            "address": self.get_remote_address(),
            "skip": cap.config["LOG_REQ_SKIP_DUMP"],
            "only": cap.config["LOG_REQ_HEADERS"],
        }

    def response_params(self):
        return {
            "skip": cap.config["LOG_RESP_SKIP_DUMP"],
            "only": cap.config["LOG_RESP_HEADERS"],
        }
