import os

from decouple import config

DEBUG = config('DEBUG', default=False)
TESTING = config('TESTING', default=DEBUG)
APP_NAME = config('APP_NAME', default="flaskel")
APP_HOST = config('APP_HOST', default='127.0.0.1')
APP_PORT = config('APP_PORT', default=5000)
FLASK_APP = config('FLASK_APP', default="app:app")
FLASK_ENV = config('FLASK_ENV', default="production")
SERVER_NAME = config('SERVER_NAME', default=f"{APP_HOST}:{APP_PORT}")

LOCALE = config('LOCALE', default="en_EN.utf8")
TEMPLATES_AUTO_RELOAD = config("TEMPLATES_AUTO_RELOAD", default=DEBUG)
EXPLAIN_TEMPLATE_LOADING = config("EXPLAIN_TEMPLATE_LOADING", default=DEBUG)

BASE_DIR = config("BASE_DIR", default=os.path.abspath(os.path.dirname(__file__)))
LOG_FILE_CONF = config("LOG_FILE_CONF", default=os.path.join('config', 'log.yaml'))

SECRET_KEY_MIN_LENGTH = 256

REQUEST_METHODS = {
    'WITHOUT_BODY': [
        'GET', 'DELETE'
    ],
    'WITH_BODY':    [
        'POST', 'PUT', 'PATCH'
    ]
}

ALLOWED_METHODS = REQUEST_METHODS['WITH_BODY'] + REQUEST_METHODS['WITHOUT_BODY']

AC_ALLOW_ORIGIN = []

RB_DEFAULT_ACCEPTABLE_MIMETYPES = [
    "application/json",
    "application/xml"
]

ERROR_PAGE = 'core/error.html'
LOG_LOGGER_NAME = FLASK_ENV
LOG_APP_NAME = APP_NAME

CF_STRICT_ACCESS = False

USE_X_SENDFILE = True
SEND_FILE_MAX_AGE_DEFAULT = 86400
ENABLE_ACCEL = True
ACCEL_BUFFERING = True
ACCEL_CHARSET = 'utf-8'
ACCEL_LIMIT_RATE = 'off'

WSGI_WERKZEUG_LINT_ENABLED = True
WSGI_WERKZEUG_PROFILER_ENABLED = True
WSGI_WERKZEUG_PROFILER_RESTRICTION = (0.1,)
WSGI_WERKZEUG_PROFILER_FILE = 'profiler.txt'

DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"

REQUEST_ID_HEADER = 'X-Request-ID'
RATELIMIT_HEADERS_ENABLED = True
LIMITER = {
    'FAIL':   '1/second',
    'FAST':   '30/minute',
    'MEDIUM': '20/minute',
    'SLOW':   '10/minute',
    'BYPASS_KEY': 'X-Limiter-Bypass',
    'BYPASS_VALUE': 'bypass-rate-limit',
}
