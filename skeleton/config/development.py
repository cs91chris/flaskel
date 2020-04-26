import os

DEBUG = True
TESTING = True

APP_HOST = "flask.local"
APP_PORT = 5000
FLASK_ENV = 'development'

SERVER_NAME = "{}:{}".format(APP_HOST, APP_PORT)

CF_STRICT_ACCESS = False

# overrides here because skeleton in the source code has a different path than the installation path
BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
LOG_FILE_CONF = os.path.join(os.path.join(BASE_DIR, 'config'), 'log.yaml')
