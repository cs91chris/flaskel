# noinspection PyUnresolvedReferences
from flask import current_app as cap

from .ext import BASE_EXTENSIONS
from .factory import AppFactory
from .standalone import Server
from .utils.http import http_status as httpcode
from .version import *
from .wsgi import WSGIBuiltin, WSGIFactory
