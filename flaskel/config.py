import os

import decouple
from vbcore import yaml
from vbcore.configurator import config
from vbcore.date_helper import Seconds
from vbcore.http.headers import ContentTypeEnum, HeaderEnum

from flaskel.utils import logger

DEBUG = config("DEBUG", default=False, cast=bool)
FLASK_DEBUG = config("FLASK_DEBUG", default=DEBUG, cast=bool)
TESTING = config("TESTING", default=False, cast=bool)
APP_NAME = config("APP_NAME", default="flaskel")
APP_HOST = config("APP_HOST", default="127.0.0.1")
APP_PORT = config("APP_PORT", default=5000, cast=int)
FLASK_APP = config("FLASK_APP", default="app:app")
SERVER_NAME = config("SERVER_NAME", default=f"{APP_HOST}:{APP_PORT}")

FLASK_ENV = config(
    "FLASK_ENV",
    default="development" if DEBUG else "production",
    cast=decouple.Choices(["development", "production"]),
)

LOCALE = config("LOCALE", default="en_EN.utf8")
TEMPLATES_AUTO_RELOAD = config("TEMPLATES_AUTO_RELOAD", default=DEBUG, cast=bool)
EXPLAIN_TEMPLATE_LOADING = config("EXPLAIN_TEMPLATE_LOADING", default=False, cast=bool)
APIDOCS_ENABLED = config("APIDOCS_ENABLED", default=True, cast=bool)
CONF_PATH = config("CONF_PATH", default=os.path.join(config.search_path, "resources"))

JWT_DEFAULT_SCOPE = None
JWT_IDENTITY_CLAIM = "identity"
JWT_DEFAULT_TOKEN_TYPE = "bearer"
JWT_ERROR_MESSAGE_KEY = "message"
JWT_QUERY_STRING_NAME = "token"
JWT_TOKEN_LOCATION = ["headers", "query_string"]
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS512")
JWT_DECODE_ALGORITHMS = config(
    "JWT_ALGORITHM", default=JWT_ALGORITHM, cast=decouple.Csv()
)
JWT_ACCESS_TOKEN_EXPIRES = config(
    "JWT_ACCESS_TOKEN_EXPIRES", default=Seconds.day, cast=int
)
JWT_REFRESH_TOKEN_EXPIRES = config(
    "JWT_REFRESH_TOKEN_EXPIRES", default=Seconds.day * 14, cast=int
)

SQLALCHEMY_DATABASE_URI = config("DATABASE_URL", default="sqlite:///db.sqlite")

MONGO_URI = config("MONGO_URI", default="mongodb://localhost:27017")
MONGO_OPTS = {
    "connectTimeoutMS": config("MONGO_CONN_TIMEOUT_MS", default=100, cast=int),
    "serverSelectionTimeoutMS": config(
        "MONGO_SERVER_SELECTION_TIMEOUT_MS", default=100, cast=int
    ),
}

REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379")
REDIS_OPTS = {
    "decode_responses": True,
    "socket_connect_timeout": config("REDIS_CONN_TIMEOUT", default=0.05, cast=float),
}

_CORS_EXPOSE_HEADERS_DEFAULT = [
    HeaderEnum.X_PAGINATION_COUNT,
    HeaderEnum.X_PAGINATION_NUM_PAGES,
    HeaderEnum.X_PAGINATION_PAGE,
    HeaderEnum.X_PAGINATION_PAGE_SIZE,
    HeaderEnum.X_REQUEST_ID,
    HeaderEnum.X_API_VERSION,
    HeaderEnum.X_RATELIMIT_RESET,
    HeaderEnum.X_RATELIMIT_REMAINING,
    HeaderEnum.X_RATELIMIT_LIMIT,
    HeaderEnum.RETRY_AFTER,
]
CORS_EXPOSE_HEADERS = config(
    "CORS_EXPOSE_HEADERS",
    default=",".join(_CORS_EXPOSE_HEADERS_DEFAULT),
    cast=decouple.Csv(),
)

BASIC_AUTH_USERNAME = config("BASIC_AUTH_USERNAME", default="admin")
BASIC_AUTH_PASSWORD = config("BASIC_AUTH_PASSWORD", default="admin")

ADMIN_EMAIL = config("ADMIN_EMAIL", default="admin@mail.com")
ADMIN_PASSWORD = config("ADMIN_PASSWORD", default="admin")

MAIL_DEBUG = config("MAIL_DEBUG", default=DEBUG, cast=bool)
MAIL_SERVER = config("MAIL_SERVER", default="127.0.0.1")
MAIL_PORT = config("MAIL_PORT", default=25, cast=int)
MAIL_USERNAME = config("MAIL_USERNAME", default="")
MAIL_PASSWORD = config("MAIL_PASSWORD", default="")
MAIL_USE_SSL = config("MAIL_USE_SSL", default=False, cast=bool)
MAIL_USE_TLS = config("MAIL_USE_TLS", default=False, cast=bool)
MAIL_DEFAULT_SENDER = config("MAIL_DEFAULT_SENDER", default=ADMIN_EMAIL)
MAIL_DEFAULT_RECEIVER = config("MAIL_DEFAULT_RECEIVER", default=ADMIN_EMAIL)
MAIL_RECIPIENT = config("MAIL_RECIPIENT", default=ADMIN_EMAIL)
MAIL_TIMEOUT = config("MAIL_TIMEOUT", default=60, cast=int)

PREFERRED_URL_SCHEME = config(
    "PREFERRED_URL_SCHEME", default="http" if FLASK_ENV == "development" else "https"
)

LOG_BUILDER = config("LOG_BUILDER", default="text")
LOG_APP_NAME = config("LOG_APP_NAME", default=APP_NAME)
LOG_LOGGER_NAME = config("LOG_LOGGER_NAME", default=FLASK_ENV)
LOG_REQ_HEADERS = config("LOG_REQ_HEADERS", default="", cast=decouple.Csv())
LOG_RESP_HEADERS = config("LOG_RESP_HEADERS", default="", cast=decouple.Csv())
LOG_REQ_SKIP_DUMP = config("LOG_REQ_SKIP_DUMP", default=not TESTING, cast=bool)
LOG_RESP_SKIP_DUMP = config("LOG_RESP_SKIP_DUMP", default=not TESTING, cast=bool)
LOG_REQ_FORMAT = config(
    "LOG_REQ_FORMAT",
    default="INCOMING REQUEST {address} {method} {scheme} {path}{headers}{body}",
)
LOG_RESP_FORMAT = config(
    "LOG_RESP_FORMAT",
    default="OUTGOING RESPONSE for {address} at {path}: STATUS {status}{headers}{body}",
)

CF_STRICT_ACCESS = config("CF_STRICT_ACCESS", default=False, cast=bool)
VERSION_STORE_MAX = config("VERSION_STORE_MAX", default=6, cast=int)
VERSION_CACHE_EXPIRE = config("VERSION_CACHE_EXPIRE", default=Seconds.hour, cast=int)

HTTP_TIMEOUT = config("HTTP_TIMEOUT", default=10, cast=int)
HTTP_SSL_VERIFY = config("HTTP_SSL_VERIFY", default=True, cast=bool)
HTTP_PROTECT_BODY = config("HTTP_PROTECT_BODY", default=False, cast=bool)
HTTP_DUMP_BODY = [
    config("HTTP_DUMP_REQ_BODY", default=False, cast=bool),
    config("HTTP_DUMP_RESP_BODY", default=False, cast=bool),
]

MAX_CONTENT_LENGTH = config("MAX_CONTENT_LENGTH", default=10 * 10**6, cast=int)
USE_X_SENDFILE = config("USE_X_SENDFILE", default=not DEBUG, cast=bool)
ENABLE_ACCEL = config("ENABLE_ACCEL", default=True, cast=bool)
ACCEL_BUFFERING = True
ACCEL_CHARSET = "utf-8"
ACCEL_LIMIT_RATE = "off"

WSGI_WERKZEUG_PROFILER_FILE = config(
    "WSGI_WERKZEUG_PROFILER_FILE", default="profiler.txt"
)
WSGI_WERKZEUG_PROFILER_RESTRICTION = config(
    "WSGI_WERKZEUG_PROFILER_RESTRICTION",
    default="0.1",
    cast=decouple.Csv(post_process=tuple),
)
WSGI_WERKZEUG_LINT_ENABLED = config(
    "WSGI_WERKZEUG_LINT_ENABLED", default=TESTING, cast=bool
)
WSGI_WERKZEUG_PROFILER_ENABLED = config(
    "WSGI_WERKZEUG_PROFILER_ENABLED", default=TESTING, cast=bool
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = config("SQLALCHEMY_ECHO", default=TESTING, cast=bool)

REQUEST_ID_HEADER = HeaderEnum.X_REQUEST_ID
RATELIMIT_ENABLED = config("RATELIMIT_ENABLED", default=not DEBUG, cast=bool)
RATELIMIT_HEADERS_ENABLED = config("RATELIMIT_HEADERS_ENABLED", default=True, cast=bool)
RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = config(
    "RATELIMIT_IN_MEMORY_FALLBACK_ENABLED", default=True, cast=bool
)

DATABASE_URL = SQLALCHEMY_DATABASE_URI
ERROR_PAGE = "core/error.html"
SECRET_KEY_FILE_NAME = ".secret.key"
SECRET_KEY_MIN_LENGTH = 256
RB_DEFAULT_ACCEPTABLE_MIMETYPES = [
    ContentTypeEnum.JSON,
]

PRETTY_DATE = "%d %B %Y %I:%M %p"
DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
SEND_FILE_MAX_AGE_DEFAULT = config(
    "SEND_FILE_MAX_AGE_DEFAULT", default=Seconds.day, cast=int
)

JSONRPC_BATCH_MAX_REQUEST = config("JSONRPC_BATCH_MAX_REQUEST", default=10, cast=int)

RATELIMIT_STORAGE_URL = config("RATELIMIT_STORAGE_URL", default=REDIS_URL)
RATELIMIT_KEY_PREFIX = config("RATELIMIT_KEY_PREFIX", default=APP_NAME)
RATELIMIT_STORAGE_OPTIONS = {
    "socket_timeout": REDIS_OPTS["socket_connect_timeout"],
    "socket_connect_timeout": REDIS_OPTS["socket_connect_timeout"],
}

IPBAN_ENABLED = config("IPBAN_ENABLED", default=True, cast=bool)
IPBAN_COUNT = config("IPBAN_COUNT", default=20, cast=int)
IPBAN_SECONDS = config("IPBAN_SECONDS", default=Seconds.hour, cast=int)
IPBAN_STATUS_CODE = config("IPBAN_STATUS_CODE", default=403, cast=int)
IPBAN_CHECK_CODES = config(
    "IPBAN_CHECK_CODES",
    default="404,405,501",
    cast=decouple.Csv(post_process=lambda items: tuple(int(i) for i in items)),
)

LIMITER = {
    "FAIL": "1/second",
    "FAST": "30/minute",
    "MEDIUM": "20/minute",
    "SLOW": "10/minute",
    "BYPASS_KEY": "X-Limiter-Bypass",
    "BYPASS_VALUE": "bypass-rate-limit",
}

SCHEDULER_JOBSTORES = {"default": {"type": "memory"}}
SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 10}
SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 20}}
SCHEDULER_AUTO_START = config("SCHEDULER_AUTO_START", default=True, cast=bool)
SCHEDULER_API_ENABLED = config("SCHEDULER_API_ENABLED", default=False, cast=bool)

CACHE_TYPE = "flask_caching.backends.redis"
CACHE_REDIS_URL = config("CACHE_REDIS_URL", default=REDIS_URL)
CACHE_DISABLED = config("CACHE_DISABLED", default=False, cast=bool)
CACHE_DEFAULT_TIMEOUT = config("CACHE_DEFAULT_TIMEOUT", default=Seconds.hour, cast=int)
CACHE_KEY_PREFIX = config("CACHE_KEY_PREFIX", default=APP_NAME)
CACHE_OPTIONS = {
    "socket_timeout": REDIS_OPTS["socket_connect_timeout"],
    "socket_connect_timeout": REDIS_OPTS["socket_connect_timeout"],
}

APISPEC = yaml.load_optional_yaml_file(
    os.path.join(CONF_PATH, "swagger.yaml"), debug=DEBUG
)
SCHEMAS = yaml.load_optional_yaml_file(
    os.path.join(CONF_PATH, "schemas.yaml"), debug=DEBUG
)
SCHEDULER_JOBS = yaml.load_optional_yaml_file(
    os.path.join(CONF_PATH, "scheduler.yaml"), debug=DEBUG
)
IPBAN_NUISANCES = yaml.load_optional_yaml_file(
    os.path.join(CONF_PATH, "nuisances.yaml"), debug=DEBUG
)
LOGGING = yaml.load_optional_yaml_file(
    os.path.join(CONF_PATH, "log.yaml"), default=logger.LOGGING
)
