class FakeLogger:
    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class DummyLogger:
    def debug(self, *args, **kwargs):
        print(*args)

    def info(self, *args, **kwargs):
        print(*args)

    def warning(self, *args, **kwargs):
        print(*args)

    def error(self, *args, **kwargs):
        print(*args)

    def exception(self, exc, *args, **kwargs):
        print(*args)
