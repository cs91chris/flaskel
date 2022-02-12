from flask import current_app as cap
from vbcore.datastruct import Dumper
from vbcore.http.httpdumper import BaseHTTPDumper


class LazyHTTPDumper(BaseHTTPDumper):
    @classmethod
    def dump_request(cls, req, *args, **kwargs):
        return Dumper(req, *args, callback=super().dump_request, **kwargs)

    @classmethod
    def dump_response(cls, resp, *args, **kwargs):
        return Dumper(resp, *args, callback=super().dump_response, **kwargs)


class FlaskelHTTPDumper(LazyHTTPDumper):
    @classmethod
    def dump_request(cls, req, *_, dump_body=None, **kwargs):
        h = cap.config.LOG_REQ_HEADERS
        return super().dump_request(req, dump_body, only_hdr=h, **kwargs)

    @classmethod
    def dump_response(cls, resp, *_, dump_body=None, **kwargs):
        h = cap.config.LOG_RESP_HEADERS
        return super().dump_response(resp, dump_body, only_hdr=h, **kwargs)
