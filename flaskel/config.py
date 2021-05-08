import os

from decouple import config, Choices

from flaskel.utils import yaml

DEBUG = config('DEBUG', default=False, cast=bool)
TESTING = config('TESTING', default=DEBUG, cast=bool)
APP_NAME = config('APP_NAME', default="flaskel")
APP_HOST = config('APP_HOST', default='127.0.0.1')
APP_PORT = config('APP_PORT', default=5000, cast=int)
FLASK_APP = config('FLASK_APP', default="app:app")
SERVER_NAME = config('SERVER_NAME', default=f"{APP_HOST}:{APP_PORT}")

FLASK_ENV = config(
    'FLASK_ENV',
    default='development' if DEBUG else 'production',
    cast=Choices(['development', 'production'])
)

LOCALE = config('LOCALE', default="en_EN.utf8")
TEMPLATES_AUTO_RELOAD = config("TEMPLATES_AUTO_RELOAD", default=DEBUG, cast=bool)
EXPLAIN_TEMPLATE_LOADING = config("EXPLAIN_TEMPLATE_LOADING", default=False, cast=bool)
APIDOCS_ENABLED = config('APIDOCS_ENABLED', default=True, cast=bool)
CONF_PATH = config('CONF_PATH', default=os.path.join('flaskel', 'scripts', 'skeleton', 'res'))

SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='sqlite:///db.sqlite')
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379')
REDIS_OPTS = {
    'socket_connect_timeout': config('REDIS_CONN_TIMEOUT', default=0.05, cast=int)
}

BASIC_AUTH_USERNAME = config('BASIC_AUTH_USERNAME', default='admin')
BASIC_AUTH_PASSWORD = config('BASIC_AUTH_PASSWORD', default='admin')

MAIL_DEBUG = DEBUG
MAIL_SERVER = config('MAIL_SERVER', default='sendria.local')
MAIL_PORT = config('MAIL_SERVER', default=62000, cast=int)
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin')
ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='admin')
MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER', default='admin@mail.com')
MAIL_DEFAULT_RECEIVER = config('MAIL_DEFAULT_RECEIVER', default='admin@mail.com')

SECRET_KEY_MIN_LENGTH = 256

RB_DEFAULT_ACCEPTABLE_MIMETYPES = [
    "application/json",
    "application/xml",
]

LOG_BUILDER = 'text'
LOG_APP_NAME = APP_NAME
LOG_SKIP_DUMP = not DEBUG
LOG_LOGGER_NAME = FLASK_ENV
ERROR_PAGE = 'core/error.html'

CF_STRICT_ACCESS = False

USE_X_SENDFILE = not DEBUG
SEND_FILE_MAX_AGE_DEFAULT = 86400
ENABLE_ACCEL = True
ACCEL_BUFFERING = True
ACCEL_CHARSET = 'utf-8'
ACCEL_LIMIT_RATE = 'off'

JWT_DEFAULT_SCOPE = None
JWT_DEFAULT_TOKEN_TYPE = 'bearer'

WSGI_WERKZEUG_LINT_ENABLED = DEBUG
WSGI_WERKZEUG_PROFILER_ENABLED = DEBUG
WSGI_WERKZEUG_PROFILER_RESTRICTION = (0.1,)
WSGI_WERKZEUG_PROFILER_FILE = 'profiler.txt'

PRETTY_DATE = "%d %B %Y %I:%M %p"
DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"

SQLALCHEMY_ECHO = DEBUG
SQLALCHEMY_TRACK_MODIFICATIONS = False
DATABASE_URL = SQLALCHEMY_DATABASE_URI

RATELIMIT_ENABLED = not DEBUG
RATELIMIT_HEADERS_ENABLED = True
RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = True
REQUEST_ID_HEADER = 'X-Request-ID'

RATELIMIT_STORAGE_URL = REDIS_URL
RATELIMIT_KEY_PREFIX = APP_NAME
RATELIMIT_STORAGE_OPTIONS = {
    'socket_timeout':         REDIS_OPTS['socket_connect_timeout'],
    'socket_connect_timeout': REDIS_OPTS['socket_connect_timeout']
}

LIMITER = {
    'FAIL':         '1/second',
    'FAST':         '30/minute',
    'MEDIUM':       '20/minute',
    'SLOW':         '10/minute',
    'BYPASS_KEY':   'X-Limiter-Bypass',
    'BYPASS_VALUE': 'bypass-rate-limit',
}

SCHEDULER_AUTO_START = False
SCHEDULER_API_ENABLED = False
SCHEDULER_JOBSTORES = {
    "default": {
        "class":     "apscheduler.jobstores.sqlalchemy:SQLAlchemyJobStore",
        "tablename": "scheduler",
        "url":       DATABASE_URL
    }
}
SCHEDULER_EXECUTORS = {
    "default": {
        "type":        "threadpool",
        "max_workers": 20
    }
}
SCHEDULER_JOB_DEFAULTS = {
    "coalesce":      False,
    "max_instances": 10
}

CACHE_TYPE = 'redis'
CACHE_REDIS_URL = REDIS_URL
CACHE_KEY_PREFIX = APP_NAME
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_OPTIONS = {
    'socket_timeout':         REDIS_OPTS['socket_connect_timeout'],
    'socket_connect_timeout': REDIS_OPTS['socket_connect_timeout']
}

LOGGING = yaml.load_optional_yaml_file(os.path.join(CONF_PATH, 'log.yaml'))
APISPEC = yaml.load_optional_yaml_file(os.path.join(CONF_PATH, 'swagger.yaml'))
SCHEMAS = yaml.load_optional_yaml_file(os.path.join(CONF_PATH, 'schemas.yaml'))
SCHEDULER_JOBS = yaml.load_optional_yaml_file(os.path.join(CONF_PATH, 'scheduler.yaml'))
IPBAN_NUISANCES = yaml.load_optional_yaml_file(os.path.join(CONF_PATH, 'nuisances.yaml'))
