DEBUG = False
TESTING = False

# add your domain here
SERVER_NAME = "flask.local:5000"

with open('.secret.key', 'r', encoding='utf-8') as f:
    SECRET_KEY = f.read()
