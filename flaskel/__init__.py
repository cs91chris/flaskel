# noinspection PyUnresolvedReferences
from flask import current_app as cap

from .ext import BASE_EXTENSIONS
from .factory import bootstrap, default_app_factory
from .standalone import serve_forever
from .utils.http import http_status as httpcode
from .version import *
