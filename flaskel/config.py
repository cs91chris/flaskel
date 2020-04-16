import os


APP_NAME = os.environ.get('APP_NAME') or "flaskel"
APP_HOST = os.environ.get('APP_HOST') or '127.0.0.1'
APP_PORT = os.environ.get('APP_PORT') or 5000
FLASK_APP = os.environ.get('FLASK_APP') or "app:app"
FLASK_ENV = os.environ.get('FLASK_ENV') or "development"

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

CONF_DIR = os.path.join(BASE_DIR, 'skeleton', 'config')
LOG_FILE_CONF = os.path.join(CONF_DIR, 'log.yaml')

REQUEST_METHODS = {
    'WITHOUT_BODY': [
        'GET', 'DELETE'
    ],
    'WITH_BODY': [
        'POST', 'PUT', 'PATCH'
    ]
}

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
ENABLE_ACCEL = True
ACCEL_BUFFERING = True
ACCEL_CHARSET = 'utf-8'
ACCEL_LIMIT_RATE = 'off'
SEND_FILE_MAX_AGE_DEFAULT = 86400
