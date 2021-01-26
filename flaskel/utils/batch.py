import asyncio
import warnings

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


class AsyncBatchExecutor:
    def __init__(self, return_exceptions=False):
        self._return_exceptions = return_exceptions

    @staticmethod
    async def _executor(fun, **kwargs):
        return fun(**kwargs)  # pragma: no cover

    @staticmethod
    def is_async(fun):
        return asyncio.iscoroutinefunction(fun)

    async def batch(self, functions):
        """

        :param functions:
        :return:
        """
        tasks = []
        for params in functions:
            func = params[0]
            args = params[1]
            if not self.is_async(func):
                tasks.append(self._executor(func, **args))  # pragma: no cover
            else:
                tasks.append(func(**args))

        return await asyncio.gather(*tasks, return_exceptions=self._return_exceptions)

    def run(self, functions):
        """

        :param functions:
        :return:
        """
        try:
            asyncio.get_running_loop()
            if not nest_asyncio:  # pragma: no cover
                raise ImportError("You must install 'nest-asyncio'")
            # noinspection PyUnresolvedReferences
            nest_asyncio.apply()  # pragma: no cover
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.batch(functions))
