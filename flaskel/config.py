# DO NOT TOUCH this file use file in ../config
#
import os


APP_NAME = os.environ.get('APP_NAME') or "flaskel"
APP_HOST = os.environ.get('APP_HOST') or '127.0.0.1'
APP_PORT = os.environ.get('APP_PORT') or 5000
FLASK_APP = os.environ.get('FLASK_APP') or "app:app"
FLASK_ENV = os.environ.get('FLASK_ENV') or "development"

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

CONF_DIR = os.path.join(BASE_DIR, 'config')
LOG_FILE_CONF = os.path.join(CONF_DIR, 'log.yaml')

JSON_ADD_STATUS = False

REQUEST_METHODS = {
    'WITHOUT_BODY': [
        'GET', 'DELETE'
    ],
    'WITH_BODY': [
        'POST', 'PUT', 'PATCH'
    ]
}

AC_ALLOW_ORIGIN = []

ALLOWED_CONTENT_TYPE = [
    "application/json"
]

