# add your domain here
#
SERVER_NAME = "flask.dev:5000"

DEBUG = False
TESTING = False

with open('.secret.key', 'r', encoding='utf-8') as f:
    SECRET_KEY = f.read()

