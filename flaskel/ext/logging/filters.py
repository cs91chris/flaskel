import logging


class FilterByArgs(logging.Filter):
    def __init__(self, *args, name=""):
        """

        :param name:
        :param args:
        """
        super().__init__(name)
        self._excluded = args

    def filter(self, record):
        """

        :param record:
        :return: False if message must be filtered
        """
        for i in self._excluded:
            if i in record.getMessage():
                return False

        return True


class PathFilter(FilterByArgs):
    def __init__(self, path, name=""):
        """

        :param path:
        :param name:
        """
        # ensure sub-paths are not accidentally excluded from logging
        super().__init__(name, f'"{path}"', f"{path} ", f"{path}?")  # json format


class OnlyPathsFilter(logging.Filter):
    def __init__(self, name="", paths=()):
        """

        :param name:
        :param paths:
        """
        super().__init__(name)
        self._only = paths

    def filter(self, record):
        """

        :param record:
        :return: False if message must be filtered
        """
        if not hasattr(record, "path"):
            return True

        # noinspection PyUnresolvedReferences
        path = record.path
        for p in self._only:
            if p == path:
                return True

        return False
