import os

DEBUG = False
TESTING = False

SERVER_NAME = os.environ.get('SERVER_NAME')
SECRET_KEY = os.environ.get('SECRET_KEY_FILE') or '.secret.key'
