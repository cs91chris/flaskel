import asyncio

import aiohttp

from . import misc
from .client import HTTPBase, httpcode


class HTTPBatchRequests(HTTPBase):
    def __init__(self, conn_timeout=60, read_timeout=60, **kwargs):
        """

        :param conn_timeout:
        :param read_timeout:
        :param kwargs:
        """
        super().__init__(**kwargs)
        self._conn_timeout = conn_timeout
        self._read_timeout = read_timeout

    async def http_request(self, session, **kwargs):
        """

        :param session:
        :param kwargs:
        :return:
        """
        try:
            async with session.request(**kwargs) as resp:
                # noinspection PyProtectedMember
                self._logger.info(misc.dump_request(resp._request_info))
                try:
                    body = await resp.json()
                except (aiohttp.ContentTypeError, ValueError, TypeError):
                    body = await resp.text()

                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError as exc:
                    self._logger.warning(misc.dump_response(resp, self._dump_body))
                    if self._raise_on_exc is True:
                        raise

                    return dict(
                        body=body,
                        status=resp.status,
                        headers={k: v for k, v in resp.headers.items()}
                    )

                self._logger.info(misc.dump_response(resp, self._dump_body))
                return dict(
                    body=body,
                    status=resp.status,
                    headers={k: v for k, v in resp.headers.items()}
                )
        except aiohttp.ClientOSError as exc:
            self._logger.exception(exc)
            if self._raise_on_exc is True:
                raise

            return dict(
                body={},
                status=httpcode.SERVICE_UNAVAILABLE,
                headers={},
                exception=exc
            )

    async def _batch(self, requests):
        """

        :param requests:
        :return:
        """
        tasks = []
        async with aiohttp.ClientSession(
                conn_timeout=self._conn_timeout,
                read_timeout=self._read_timeout
        ) as session:
            for params in requests:
                tasks.append(self.http_request(session, **params))

            return await asyncio.gather(*tasks, return_exceptions=not self._raise_on_exc)

    def request(self, requests, **kwargs):
        """

        :param requests:
        :return:
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._batch(requests))
