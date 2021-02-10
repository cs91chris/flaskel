import asyncio

import aiohttp
import flask

from flaskel import cap
from flaskel.utils.batch import AsyncBatchExecutor
from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.uuid import get_uuid
from .client import HTTPBase, httpcode
from .httpdumper import FlaskelHTTPDumper


class HTTPBatch(HTTPBase, AsyncBatchExecutor):
    def __init__(self, conn_timeout=10, read_timeout=10, **kwargs):
        """

        :param conn_timeout:
        :param read_timeout:
        :param kwargs:
        """
        HTTPBase.__init__(self, **kwargs)
        AsyncBatchExecutor.__init__(self, return_exceptions=not self._raise_on_exc)
        self._timeout = aiohttp.ClientTimeout(sock_read=read_timeout, sock_connect=conn_timeout)

    async def http_request(self, dump_body=None, timeout=None, **kwargs):
        """

        :param dump_body:
        :param timeout:
        :param kwargs:
        :return:
        """
        if dump_body is None:
            dump_body = self._dump_body

        if timeout is None:
            timeout = self._timeout
        elif not isinstance(timeout, aiohttp.ClientTimeout):
            timeout = aiohttp.ClientTimeout(sock_read=timeout, sock_connect=timeout)

        try:
            self._logger.info(self.dump_request(ObjectDict(**kwargs), dump_body))
            async with aiohttp.ClientSession(timeout=timeout) as session, \
                    session.request(**kwargs) as resp:
                try:
                    body = await resp.json()
                except (aiohttp.ContentTypeError, ValueError, TypeError):
                    body = await resp.text()

                try:
                    response = ObjectDict(
                        body=body, status=resp.status,
                        headers={k: v for k, v in resp.headers.items()}
                    )
                    log_resp = response
                    log_resp.text = response.body
                    log_resp = self.dump_response(log_resp, dump_body)
                    resp.raise_for_status()
                    self._logger.info(log_resp)
                except aiohttp.ClientResponseError as exc:
                    self._logger.warning(log_resp)
                    if self._raise_on_exc is True:
                        raise  # pragma: no cover
                    response.exception = exc
                return response
        except (aiohttp.ClientError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as exc:
            self._logger.exception(exc)
            if self._raise_on_exc is True:
                raise  # pragma: no cover

            return ObjectDict(
                body={}, status=httpcode.SERVICE_UNAVAILABLE,
                headers={}, exception=exc
            )

    def request(self, requests, **kwargs):
        """

        :param requests:
        :return:
        """
        _requests = []
        for r in requests:
            r.setdefault('method', 'GET')
            self._tasks.append((self.http_request, r))

        return self.run()


class FlaskelHTTPBatch(HTTPBatch, FlaskelHTTPDumper):
    def __init__(self, **kwargs):
        kwargs.setdefault('logger', cap.logger)
        kwargs.setdefault('conn_timeout', cap.config.HTTP_TIMEOUT or 10)
        kwargs.setdefault('read_timeout', cap.config.HTTP_TIMEOUT or 10)
        super().__init__(**kwargs)

    def request(self, requests, **kwargs):
        if flask.request.id:
            for r in requests:
                if not r.get('headers'):
                    r['headers'] = {}
                req_id = f"{flask.request.id},{get_uuid()}"
                r['headers'][cap.config.REQUEST_ID_HEADER] = req_id

        return super().request(requests, **kwargs)
