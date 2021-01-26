import asyncio

import flask

from flaskel import cap
from flaskel.utils.batch import aiohttp, AsyncBatchExecutor
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
        self._timeout = aiohttp.ClientTimeout(
            sock_read=read_timeout,
            sock_connect=conn_timeout
        )

    async def http_request(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        if not aiohttp:
            raise ImportError("You must install 'aiohttp'")  # pragma: no cover
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session, \
                    session.request(**kwargs) as resp:
                # noinspection PyProtectedMember
                self._logger.info(self.dump_request(ObjectDict(**kwargs), self._dump_body))
                try:
                    body = await resp.json()
                except (aiohttp.ContentTypeError, ValueError, TypeError):
                    body = await resp.text()

                try:
                    response = ObjectDict(
                        body=body,
                        status=resp.status,
                        headers={k: v for k, v in resp.headers.items()}
                    )
                    resp.raise_for_status()
                except aiohttp.ClientResponseError as exc:
                    self._logger.warning(self.dump_response(response, self._dump_body))
                    if self._raise_on_exc is True:
                        raise  # pragma: no cover

                    response.exception = exc
                    return response

                self._logger.info(self.dump_response(response, self._dump_body))
                return response
        except (aiohttp.ClientError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as exc:
            self._logger.exception(exc)
            if self._raise_on_exc is True:
                raise  # pragma: no cover

            return ObjectDict(
                body={},
                status=httpcode.SERVICE_UNAVAILABLE,
                headers={},
                exception=exc
            )

    def request(self, requests, **kwargs):
        """

        :param requests:
        :return:
        """
        _requests = []
        for r in requests:
            r.setdefault('method', 'GET')
            _requests.append((self.http_request, r))

        return self.run(_requests)


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
