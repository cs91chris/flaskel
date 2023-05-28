from .base import LogBuilder
from .json import LogJSONBuilder
from .text import LogTextBuilder


def builder_factory(name):
    if name == "text":
        return LogTextBuilder()
    if name == "json":
        return LogJSONBuilder()
