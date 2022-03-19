import typing as t

from requests import exceptions as http_exc
from vbcore.datastruct import Dumper
from vbcore.http.batch import HTTPBatch
from vbcore.http.client import HTTPClient, JsonRPCClient
from vbcore.http.httpdumper import BaseHTTPDumper
from vbcore.uuid import get_uuid

from flaskel import cap, request

HTTPStatusError = (http_exc.HTTPError,)
NetworkError = (http_exc.ConnectionError, http_exc.Timeout)
all_errors = (*HTTPStatusError, *NetworkError)


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


class FlaskelHttpBatch(FlaskelHTTPDumper, HTTPBatch):
    def __init__(self, endpoint: t.Optional[str] = None, **kwargs):
        kwargs.setdefault("logger", cap.logger)
        kwargs.setdefault("timeout", cap.config.HTTP_TIMEOUT or 10)
        super().__init__(endpoint, **kwargs)

    def request(self, requests, **kwargs):
        if request.id:
            for r in requests:
                if not r.get("headers"):
                    r["headers"] = {}
                req_id = f"{request.id},{get_uuid()}"
                r["headers"][cap.config.REQUEST_ID_HEADER] = req_id

        kwargs.setdefault("verify", cap.config.HTTP_SSL_VERIFY)
        return super().request(requests, **kwargs)


class FlaskelHttp(FlaskelHTTPDumper, HTTPClient):
    def __init__(self, endpoint, *args, **kwargs):
        kwargs.setdefault("logger", cap.logger)
        super().__init__(endpoint, *args, **kwargs)
        self._timeout = cap.config.HTTP_TIMEOUT or self._timeout

    def request(self, uri, **kwargs):
        if request.id:
            if not kwargs.get("headers"):
                kwargs["headers"] = {}
            kwargs["headers"][cap.config.REQUEST_ID_HEADER] = request.id

        kwargs.setdefault("verify", cap.config.HTTP_SSL_VERIFY)
        return super().request(uri, **kwargs)


class FlaskelJsonRPC(FlaskelHttp, JsonRPCClient):
    pass
