# pylint: disable=all
class FakeLogger:
    def debug(self, *args, **kwargs):
        """do nothing"""

    def info(self, *args, **kwargs):
        """do nothing"""

    def warning(self, *args, **kwargs):
        """do nothing"""

    def error(self, *args, **kwargs):
        """do nothing"""

    def exception(self, *args, **kwargs):
        """do nothing"""


# noinspection PyMethodMayBeStatic
class DummyLogger:
    def debug(self, *args, **__):
        print("DEBUG:", *args)

    def info(self, *args, **__):
        print("INFO:", *args)

    def warning(self, *args, **__):
        print("WARNING:", *args)

    def error(self, *args, **__):
        print("ERROR:", *args)

    def exception(self, _, *args, **__):
        print("CRITICAL:", *args)
