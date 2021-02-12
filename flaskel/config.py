from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
TESTING = config('TESTING', default=DEBUG, cast=bool)
APP_NAME = config('APP_NAME', default="flaskel")
APP_HOST = config('APP_HOST', default='127.0.0.1')
APP_PORT = config('APP_PORT', default=5000, cast=int)
FLASK_APP = config('FLASK_APP', default="app:app")
FLASK_ENV = config('FLASK_ENV', default='development' if DEBUG else 'production')
SERVER_NAME = config('SERVER_NAME', default=f"{APP_HOST}:{APP_PORT}")

LOCALE = config('LOCALE', default="en_EN.utf8")
TEMPLATES_AUTO_RELOAD = config("TEMPLATES_AUTO_RELOAD", default=DEBUG, cast=bool)
EXPLAIN_TEMPLATE_LOADING = config("EXPLAIN_TEMPLATE_LOADING", default=DEBUG, cast=bool)

SECRET_KEY_MIN_LENGTH = 256

AC_ALLOW_ORIGIN = []

RB_DEFAULT_ACCEPTABLE_MIMETYPES = [
    "application/json",
    "application/xml",
]

ERROR_PAGE = 'core/error.html'
LOG_LOGGER_NAME = FLASK_ENV
LOG_APP_NAME = APP_NAME

CF_STRICT_ACCESS = False

USE_X_SENDFILE = DEBUG
SEND_FILE_MAX_AGE_DEFAULT = 86400
ENABLE_ACCEL = True
ACCEL_BUFFERING = True
ACCEL_CHARSET = 'utf-8'
ACCEL_LIMIT_RATE = 'off'

WSGI_WERKZEUG_LINT_ENABLED = DEBUG
WSGI_WERKZEUG_PROFILER_ENABLED = DEBUG
WSGI_WERKZEUG_PROFILER_RESTRICTION = (0.1,)
WSGI_WERKZEUG_PROFILER_FILE = 'profiler.txt'

DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"

REQUEST_ID_HEADER = 'X-Request-ID'
RATELIMIT_HEADERS_ENABLED = True
LIMITER = {
    'FAIL':         '1/second',
    'FAST':         '30/minute',
    'MEDIUM':       '20/minute',
    'SLOW':         '10/minute',
    'BYPASS_KEY':   'X-Limiter-Bypass',
    'BYPASS_VALUE': 'bypass-rate-limit',
}
