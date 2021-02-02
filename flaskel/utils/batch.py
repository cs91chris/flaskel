import asyncio

import nest_asyncio


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
        for f in functions:
            try:
                if len(f) > 1:
                    func, args = f[0], f[1] or {}
                else:
                    func, args = f[0], {}
            except TypeError:
                func, args = f, {}

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
            nest_asyncio.apply()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.batch(functions))
