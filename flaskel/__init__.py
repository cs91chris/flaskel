# noinspection PyUnresolvedReferences
from flask import current_app as cap

from flaskel.http import http_status as httpcode
from flaskel.tester import TestClient
from flaskel.utils import datastruct
from .builder import AppBuilder
from .ext import BASE_EXTENSIONS
from .flaskel import Flaskel
from .standalone import Server
from .version import *
from .wsgi import WSGIFactory
