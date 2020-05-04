class FakeLogger:
    def debug(self, *args):
        pass

    def info(self, *args):
        pass

    def warning(self, *args):
        pass

    def error(self, *args):
        pass

    def exception(self, *args):
        pass


# noinspection PyMethodMayBeStatic
class DummyLogger:
    def debug(self, *args):
        print(*args)

    def info(self, *args):
        print(*args)

    def warning(self, *args):
        print(*args)

    def error(self, *args):
        print(*args)

    def exception(self, *args):
        print(*args)
