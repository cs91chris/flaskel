import os

import pytest
from scripts.cli import APP_CONFIG

from flaskel import ObjectDict, TestClient
from flaskel.ext.sqlalchemy.support import SQLASupport
from . import helpers as h

__all__ = [
    "h",
    "testapp",
    "test_client",
    "auth_token",
]

DB_TEST = "test.sqlite"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLE_DATA = os.path.join(BASE_DIR, "..", "res", "sample.sql")
CONFIG = ObjectDict()

CONFIG.MAIL_DEBUG = True
CONFIG.CACHE_TYPE = "null"
CONFIG.RATELIMIT_ENABLED = False
CONFIG.SQLALCHEMY_ECHO = True
CONFIG.SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_TEST}"

CONFIG.SENDRIA = dict(
    endpoint="http://sendria.local:61000/api/messages",
    username="guest123",
    password="guest123",
)


def load_sample_data():
    SQLASupport.exec_from_file(
        CONFIG.SQLALCHEMY_DATABASE_URI, SAMPLE_DATA, CONFIG.SQLALCHEMY_ECHO
    )


EXTRAS = dict(
    conf=CONFIG,
    template_folder="blueprints/web/templates",
    static_folder="blueprints/web/static",
    callback=load_sample_data,
)


@pytest.fixture(scope="session")
def testapp():
    try:
        os.remove(DB_TEST)
    except OSError as exc:
        print(str(exc))

    return TestClient.get_app(**{**APP_CONFIG, **EXTRAS})


@pytest.fixture(scope="session")
def test_client(testapp):
    return testapp.test_client()


@pytest.fixture()
def auth_token(test_client):
    def get_access_token(token=None, email=None, password=None, in_query=True):
        if token is not None:
            if in_query is True:
                return f"jwt={token}"
            return dict(Authorization=f"Bearer {token}")

        credentials = dict(
            email=email or h.config.ADMIN_EMAIL,
            password=password or h.config.ADMIN_PASSWORD,
        )
        tokens = test_client.post(h.url_for(h.VIEWS.access_token), json=credentials)
        if in_query is True:
            return f"jwt={tokens.json.access_token}"
        return dict(Authorization=f"Bearer {tokens.json.access_token}")

    return get_access_token
