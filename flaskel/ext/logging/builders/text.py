from abc import ABC

import flask
from flask import current_app as cap

from .base import BaseWrapper, LogBuilder


class Wrapper(BaseWrapper, ABC):
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
        if only:
            hdr = {k: hdr[k] for k in only if k in hdr}

        headers = "\n".join(f"{k}: {v}" for k, v in hdr.items())
        return f"\n{headers}" if headers else headers

    @staticmethod
    def dump_body(r):
        """
        dump http body as plain text

        :param r: Response object
        :return:
        """
        try:
            body = r.get_data(as_text=True)
        except UnicodeError:
            body = "body not dumped: invalid encoding or binary file"
        return f"\n{body}" if body else body


class RequestWrap(Wrapper):
    def dump(self):
        body = ""
        headers = ""
        request = self.data
        hdr = self.opts.get("only")
        skip = self.opts.get("skip")
        fmt = self.opts.get("fmt") or ""

        if "{headers}" in fmt and (hdr or not skip):
            headers = self.dump_headers(request.headers, hdr)
        if "{body}" in fmt and not skip:
            body = self.dump_body(request)

        return fmt.format(
            address=self.opts.get("addr"),
            method=request.method,
            scheme=request.scheme,
            path=request.full_path,
            headers=headers,
            body=body,
        )


class ResponseWrap(Wrapper):
    def dump(self):
        body = ""
        headers = ""
        response = self.data
        hdr = self.opts.get("only")
        skip = self.opts.get("skip")
        fmt = self.opts.get("fmt") or ""

        if "{headers}" in fmt and (hdr or not skip):
            headers = self.dump_headers(response.headers, hdr)
        if "{body}" in fmt and not skip:
            body = self.dump_body(response)

        return fmt.format(
            status=response.status,
            path=flask.request.path,
            level=self.opts.get("level"),
            address=self.opts.get("addr"),
            headers=headers,
            body=body,
        )


class LogTextBuilder(LogBuilder):
    wrapper_dump_request = RequestWrap
    wrapper_dump_response = ResponseWrap

    def request_params(self):
        return {
            "addr": self.get_remote_address(),
            "skip": cap.config["LOG_REQ_SKIP_DUMP"],
            "only": cap.config["LOG_REQ_HEADERS"],
            "fmt": cap.config["LOG_REQ_FORMAT"],
        }

    def response_params(self):
        return {
            "addr": self.get_remote_address(),
            "skip": cap.config["LOG_RESP_SKIP_DUMP"],
            "only": cap.config["LOG_RESP_HEADERS"],
            "fmt": cap.config["LOG_RESP_FORMAT"],
        }
