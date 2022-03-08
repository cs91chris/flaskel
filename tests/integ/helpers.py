import os

from vbcore import yaml
from vbcore.datastruct import ObjectDict

from flaskel import cap

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "data")
DB_TEST = os.path.join(SAMPLE_DIR, "test.sqlite")


class HOSTS:
    fake = "http://localhost"
    apitester = "https://httpbin.org"


def after_request_hook(response):
    cap.logger.info("AFTER_REQUEST_HOOK")
    return response


def before_request_hook():
    cap.logger.info("BEFORE_REQUEST_HOOK")


def prepare_config(conf=None):
    config = ObjectDict()
    config.CACHE_TYPE = "null"
    config.SQLALCHEMY_ECHO = True
    config.RATELIMIT_ENABLED = False
    config.CONF_PATH = str(SAMPLE_DIR)
    config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_TEST}"
    config.APISPEC = yaml.load_yaml_file(os.path.join(SAMPLE_DIR, "swagger.yaml"))
    config.SENDRIA = dict(
        endpoint="http://sendria.local:61000/api/messages",
        username="guest123",
        password="guest123",
    )

    config.update(conf or {})
    return config
