import os

DEBUG = bool(os.environ.get('DEBUG') or False)
TESTING = bool(os.environ.get('TESTING') or DEBUG)
APP_NAME = os.environ.get('APP_NAME') or "flaskel"
APP_HOST = os.environ.get('APP_HOST') or '127.0.0.1'
APP_PORT = int(os.environ.get('APP_PORT') or 5000)
FLASK_APP = os.environ.get('FLASK_APP') or "app:app"
FLASK_ENV = os.environ.get('FLASK_ENV') or "production"
SERVER_NAME = os.environ.get('SERVER_NAME') or "{}:{}".format(APP_HOST, APP_PORT)

LOCALE = 'en_EN.utf8'
TEMPLATES_AUTO_RELOAD = DEBUG
EXPLAIN_TEMPLATE_LOADING = DEBUG

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE_CONF = os.path.join('config', 'log.yaml')

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
