# pylint: disable=redefined-outer-name

import os

import pytest
from flask import Config
from scripts.cli import APP_CONFIG
from vbcore.datastruct import ObjectDict
from vbcore.db.support import SQLASupport

from flaskel.tester import helpers as h, TestClient
from flaskel.tester.helpers import ApiTester

from .helpers import Views

DB_TEST = "test.sqlite"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLE_DATA = os.path.join(BASE_DIR, "..", "resources", "sample.sql")
CONFIG = ObjectDict()

CONFIG.DEBUG = True
CONFIG.TESTING = True
CONFIG.MAIL_DEBUG = True
CONFIG.CACHE_TYPE = "null"
CONFIG.RATELIMIT_ENABLED = False
CONFIG.SQLALCHEMY_ECHO = True
CONFIG.SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_TEST}"


def load_sample_data():
    SQLASupport.exec_from_file(
        CONFIG.SQLALCHEMY_DATABASE_URI, SAMPLE_DATA, CONFIG.SQLALCHEMY_ECHO
    )


@pytest.fixture(scope="session")
def testapp():
    try:
        os.remove(DB_TEST)
    except OSError as exc:
        print(str(exc))

    config = Config(".")
    config.from_pyfile("{skeleton}/scripts/config.py")
    config.from_mapping(CONFIG)

    extras = dict(
        conf=ObjectDict(**config),
        template_folder="{skeleton}/views/web/templates",
        static_folder="{skeleton}/views/web/static",
        after_create_hook=load_sample_data,
    )

    return TestClient.get_app(**{**APP_CONFIG, **extras})


@pytest.fixture(scope="session")
def test_client(testapp):
    return testapp.test_client()


@pytest.fixture(scope="session")
def config(testapp):
    return testapp.config


@pytest.fixture(scope="session")
def api_tester(test_client):
    return ApiTester(test_client)


@pytest.fixture(scope="session")
def views():
    return Views


@pytest.fixture()
def auth_token(test_client, views):
    def get_access_token(token=None, email=None, password=None, in_query=True):
        if token is not None:
            if in_query is True:
                return f"token={token}"
            return dict(Authorization=f"Bearer {token}")

        credentials = dict(
            email=email or h.config.ADMIN_EMAIL,
            password=password or h.config.ADMIN_PASSWORD,
        )
        tokens = test_client.post(h.url_for(views.access_token), json=credentials)
        if in_query is True:
            return f"token={tokens.json.access_token}"
        return dict(Authorization=f"Bearer {tokens.json.access_token}")

    return get_access_token
