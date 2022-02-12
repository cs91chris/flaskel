# noinspection PyUnresolvedReferences
from flask import current_app as cap

# noinspection PyUnresolvedReferences
from vbcore.http import httpcode, HttpMethod

# noinspection PyUnresolvedReferences
from .builder import AppBuilder
from .flaskel import Flaskel, Request, Response

# noinspection PyUnresolvedReferences
from .standalone import Server

# noinspection PyUnresolvedReferences
from .tester import TestClient

# noinspection PyUnresolvedReferences
from .utils import webargs

# noinspection PyUnresolvedReferences
from .utils.datastruct import ConfigProxy, ExtProxy

# noinspection PyUnresolvedReferences
from .version import *  # noqa: F403
