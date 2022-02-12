import flask
from requests import exceptions as http_exc
from vbcore.http.batch import HTTPBatch
from vbcore.http.client import HTTPClient, JsonRPCClient
from vbcore.uuid import get_uuid

from flaskel import flaskel
from .httpdumper import FlaskelHTTPDumper

HTTPStatusError = (http_exc.HTTPError,)
NetworkError = (http_exc.ConnectionError, http_exc.Timeout)
all_errors = (*HTTPStatusError, *NetworkError)

cap = flaskel.cap
request: "flaskel.Request" = flask.request  # type: ignore


class FlaskelHTTPBatch(FlaskelHTTPDumper, HTTPBatch):
    def __init__(self, **kwargs):
        kwargs.setdefault("logger", cap.logger)
        kwargs.setdefault("conn_timeout", cap.config.HTTP_TIMEOUT or 10)
        kwargs.setdefault("read_timeout", cap.config.HTTP_TIMEOUT or 10)
        super().__init__(**kwargs)

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
