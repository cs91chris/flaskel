import os

DEBUG = False
TESTING = False
FLASK_ENV = 'production'
APP_HOST = "flask.local"
APP_PORT = 5000

SERVER_NAME = os.environ.get('SERVER_NAME') or "{}:{}".format(APP_HOST, APP_PORT)

# in production env secret key should be saved in a file
SECRET_KEY = os.environ.get('SECRET_KEY_FILE')

# overrides here because skeleton in the source code has a different path than the installation path
BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
LOG_FILE_CONF = os.path.join(os.path.join(BASE_DIR, 'config'), 'log.yaml')
