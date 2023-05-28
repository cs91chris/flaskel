import logging


class FilterByArgs(logging.Filter):
    def __init__(self, *args, name=""):
        super().__init__(name)
        self._excluded = args

    def filter(self, record):
        for i in self._excluded:
            if i in record.getMessage():
                return False

        return True


class PathFilter(FilterByArgs):
    def __init__(self, path, name=""):
        # ensure sub-paths are not accidentally excluded from logging
        super().__init__(name, f'"{path}"', f"{path} ", f"{path}?")  # json format


class OnlyPathsFilter(logging.Filter):
    def __init__(self, name="", paths=()):
        super().__init__(name)
        self._only = paths

    def filter(self, record):
        if not hasattr(record, "path"):
            return True

        # noinspection PyUnresolvedReferences
        path = record.path
        for p in self._only:
            if p == path:
                return True

        return False
