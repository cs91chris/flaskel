import asyncio
import threading

import nest_asyncio


class BatchExecutor:
    def __init__(self, tasks=None):
        """

        :param tasks:
        """
        self._tasks = tasks or []

    @staticmethod
    def prepare_task(task):
        """

        :param task:
        :return:
        """
        try:
            if len(task) > 1:
                return task[0], task[1] or {}
            else:
                return task[0], {}
        except TypeError:
            return task, {}

    def run(self):
        responses = []
        for task in self._tasks:
            func, args = self.prepare_task(task)
            responses.append(func(**args))
        return responses


class AsyncBatchExecutor(BatchExecutor):
    def __init__(self, return_exceptions=False, **kwargs):
        """

        :param tasks:
        :param return_exceptions:
        """
        super().__init__(**kwargs)
        self._return_exceptions = return_exceptions

    @staticmethod
    async def _executor(fun, **kwargs):
        return fun(**kwargs)  # pragma: no cover

    @staticmethod
    def is_async(fun):
        return asyncio.iscoroutinefunction(fun)

    async def batch(self):
        tasks = []
        for task in self._tasks:
            func, args = self.prepare_task(task)
            if not self.is_async(func):
                tasks.append(self._executor(func, **args))  # pragma: no cover
            else:
                tasks.append(func(**args))

        return await asyncio.gather(*tasks, return_exceptions=self._return_exceptions)

    def run(self):
        try:
            asyncio.get_running_loop()
            nest_asyncio.apply()  # pragma: no cover
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.batch())


class Thread(threading.Thread):
    def __init__(self, runnable, params=None, daemon=False, *args, **kwargs):
        """

        :param fun:
        :param params:
        """
        super().__init__(**kwargs)
        self._runnable = runnable
        self._args = args
        self._params = params or {}
        self.response = None
        self.daemon = daemon

    def run(self):
        self.response = self._runnable(*self._args, **self._params)


class DaemonThread(threading.Thread):
    def __init__(self, runnable, params=None, *args, **kwargs):
        """

        :param runnable:
        :param params:
        """
        super().__init__(**kwargs)
        self.daemon = True
        self._runnable = runnable
        self._args = args
        self._params = params or {}

    def run(self):
        self._runnable(*self._args, **self._params)


class ThreadBatchExecutor(BatchExecutor):
    def __init__(self, thread_class=None, single_thread=False, **kwargs):
        """

        :param thread_class:
        """
        super().__init__(**kwargs)
        self._single_thread = single_thread
        self._thread_class = thread_class or Thread

        if self._single_thread:
            self._tasks[0] = self._thread_class(super().run)
            return

        for i, t in enumerate(self._tasks):
            if isinstance(t, dict):
                thread = self._thread_class(**t)
            else:
                func, args = self.prepare_task(t)
                thread = self._thread_class(func, params=args)
            self._tasks[i] = thread

    def run(self):
        for t in self._tasks:
            t.start()

        for t in self._tasks:
            if t.daemon is False:
                t.join()
            else:
                return

        if self._single_thread:
            return self._tasks[0].response

        return [t.response for t in self._tasks]
