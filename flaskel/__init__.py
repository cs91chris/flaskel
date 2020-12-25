# noinspection PyUnresolvedReferences
from flask import current_app as cap

from flaskel.http import http_status as httpcode
from .ext import BASE_EXTENSIONS
from .factory import AppFactory
from .standalone import Server
from .version import *
from .wsgi import WSGIBuiltin, WSGIFactory
