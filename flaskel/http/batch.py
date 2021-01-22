import asyncio
import warnings

import flask

from flaskel import cap
from flaskel.utils.datastruct import ObjectDict
from flaskel.utils.uuid import get_uuid
from .client import HTTPBase, httpcode
from .httpdumper import FlaskelHTTPDumper

try:
    import aiohttp
except ImportError as err:  # pragma: no cover
    warnings.warn(str(err))
    aiohttp = None

try:
    import nest_asyncio
except ImportError as err:  # pragma: no cover
    warnings.warn(str(err))
    nest_asyncio = None


class HTTPBatch(HTTPBase):
    def __init__(self, conn_timeout=60, read_timeout=60, **kwargs):
        """

        :param conn_timeout:
        :param read_timeout:
        :param kwargs:
        """
        super().__init__(**kwargs)
        self._timeout = aiohttp.ClientTimeout(
            sock_read=read_timeout,
            sock_connect=conn_timeout
        )

    async def http_request(self, session, **kwargs):
        """

        :param session:
        :param kwargs:
        :return:
        """
        if not aiohttp:
            raise ImportError("You must install 'aiohttp'")  # pragma: no cover
        try:
            async with session.request(**kwargs) as resp:
                # noinspection PyProtectedMember
                self._logger.info(self.dump_request(resp._request_info, self._dump_body))
                try:
                    body = await resp.json()
                except (aiohttp.ContentTypeError, ValueError, TypeError):
                    body = await resp.text()

                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError as exc:
                    self._logger.warning(self.dump_response(resp, self._dump_body))
                    if self._raise_on_exc is True:
                        raise  # pragma: no cover

                    return ObjectDict(
                        body=body,
                        status=resp.status,
                        headers={k: v for k, v in resp.headers.items()},
                        exception=exc
                    )

                self._logger.info(self.dump_response(resp, self._dump_body))
                return ObjectDict(
                    body=body,
                    status=resp.status,
                    headers={k: v for k, v in resp.headers.items()}
                )
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

    async def batch(self, requests):
        """

        :param requests:
        :return:
        """
        tasks = []
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            for params in requests:
                tasks.append(self.http_request(session, **params))

            return await asyncio.gather(*tasks, return_exceptions=not self._raise_on_exc)

    def request(self, requests, **kwargs):
        """

        :param requests:
        :return:
        """
        if not aiohttp:
            raise ImportError("You must install 'aiohttp'")  # pragma: no cover

        try:
            asyncio.get_running_loop()
            if not nest_asyncio:  # pragma: no cover
                raise ImportError("You must install 'nest-asyncio'")
            # noinspection PyUnresolvedReferences
            nest_asyncio.apply()  # pragma: no cover
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.batch(requests))


class FlaskelHTTPBatch(HTTPBatch, FlaskelHTTPDumper):
    def __init__(self, **kwargs):
        kwargs.setdefault('logger', cap.logger)
        super().__init__(**kwargs)

    def request(self, requests, **kwargs):
        if flask.request.id:
            for r in requests:
                if not r.get('headers'):
                    r['headers'] = {}
                req_id = f"{flask.request.id},{get_uuid()}"
                r['headers'][cap.config.REQUEST_ID_HEADER] = req_id

        return super().request(requests, **kwargs)
