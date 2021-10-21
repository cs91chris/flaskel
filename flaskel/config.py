import os
from collections import OrderedDict

import decouple

from flaskel.utils import logger, yaml, Seconds

_conf_search_path = os.environ.get("ENV_PATH")
_conf_file_name = os.environ.get("ENV_FILE")
_conf_file_encoding = os.environ.get("ENV_FILE_ENCODING")


class AutoConfig(decouple.AutoConfig):
    encoding = _conf_file_encoding or "UTF-8"

    SUPPORTED = OrderedDict(
        [
            (_conf_file_name or "settings.ini", decouple.RepositoryIni),
            (_conf_file_name or ".env", decouple.RepositoryEnv),
        ]
    )


config = AutoConfig(search_path=_conf_search_path or os.getcwd())

DEBUG = config("DEBUG", default=False, cast=bool)
TESTING = config("TESTING", default=DEBUG, cast=bool)
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
CONF_PATH = config(
    "CONF_PATH", default=os.path.join("flaskel", "scripts", "skeleton", "resources")
)

JWT_TOKEN_LOCATION = ["headers", "query_string"]
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
    "X-Pagination-Count",
    "X-Pagination-Num-Pages",
    "X-Pagination-Page",
    "X-Pagination-Page-Size",
    "X-Request-ID",
    "X-Api-Version",
    "X-RateLimit-Reset",
    "X-RateLimit-Remaining",
    "X-RateLimit-Limit",
    "Retry-After",
]
CORS_EXPOSE_HEADERS = config(
    "CORS_EXPOSE_HEADERS",
    default=",".join(_CORS_EXPOSE_HEADERS_DEFAULT),
    cast=decouple.Csv(),
)

BASIC_AUTH_USERNAME = config("BASIC_AUTH_USERNAME", default="admin")
BASIC_AUTH_PASSWORD = config("BASIC_AUTH_PASSWORD", default="admin")

MAIL_DEBUG = config("MAIL_DEBUG", default=DEBUG, cast=bool)
MAIL_SERVER = config("MAIL_SERVER", default="sendria.local")
MAIL_PORT = config("MAIL_SERVER", default=62000, cast=int)
ADMIN_EMAIL = config("ADMIN_EMAIL", default="admin@mail.com")
ADMIN_PASSWORD = config("ADMIN_PASSWORD", default="admin")
MAIL_DEFAULT_SENDER = config("MAIL_DEFAULT_SENDER", default="admin@mail.com")
MAIL_DEFAULT_RECEIVER = config("MAIL_DEFAULT_RECEIVER", default="admin@mail.com")

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

REQUEST_ID_HEADER = "X-Request-ID"
RATELIMIT_ENABLED = config("RATELIMIT_ENABLED", default=not DEBUG, cast=bool)
RATELIMIT_HEADERS_ENABLED = config("RATELIMIT_HEADERS_ENABLED", default=True, cast=bool)
RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = config(
    "RATELIMIT_IN_MEMORY_FALLBACK_ENABLED", default=True, cast=bool
)

DATABASE_URL = SQLALCHEMY_DATABASE_URI
ERROR_PAGE = "core/error.html"
SECRET_KEY_MIN_LENGTH = 256
RB_DEFAULT_ACCEPTABLE_MIMETYPES = [
    "application/json",
    "application/xml",
]

JWT_DEFAULT_SCOPE = None
JWT_DEFAULT_TOKEN_TYPE = "bearer"
PRETTY_DATE = "%d %B %Y %I:%M %p"
DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
SEND_FILE_MAX_AGE_DEFAULT = config(
    "SEND_FILE_MAX_AGE_DEFAULT", default=Seconds.day, cast=int
)

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

SCHEDULER_AUTO_START = config("SCHEDULER_AUTO_START", default=True, cast=bool)
SCHEDULER_API_ENABLED = config("SCHEDULER_API_ENABLED", default=False, cast=bool)
SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 20}}
SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 10}
SCHEDULER_JOBSTORES = {
    "default": {
        "class": "apscheduler.jobstores.sqlalchemy:SQLAlchemyJobStore",
        "tablename": "scheduler",
        "url": DATABASE_URL,
    }
}

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
