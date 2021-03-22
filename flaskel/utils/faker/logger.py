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


# noinspection PyMethodMayBeStatic
class DummyLogger:
    def debug(self, *args, **kwargs):
        print("DEBUG:", *args)

    def info(self, *args, **kwargs):
        print("INFO:", *args)

    def warning(self, *args, **kwargs):
        print("WARNING:", *args)

    def error(self, *args, **kwargs):
        print("ERROR:", *args)

    def exception(self, exc, *args, **kwargs):
        print("CRITICAL:", *args)
