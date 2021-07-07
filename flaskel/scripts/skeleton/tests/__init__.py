import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.sql import text as execute_sql

from flaskel import TestClient
from flaskel.utils import yaml
from scripts.cli import APP_CONFIG
from . import helpers as h

DB_TEST = 'test.sqlite'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONF_DIR = os.path.join(BASE_DIR, '..', 'res')
CONF_FILE = os.path.join(CONF_DIR, 'conf.yaml')
SAMPLE_DATA = os.path.join(CONF_DIR, 'sample.sql')

CONFIG = yaml.load_yaml_file(CONF_FILE)

CONFIG.app.CACHE_TYPE = 'null'
CONFIG.app.RATELIMIT_ENABLED = False
CONFIG.app.SQLALCHEMY_ECHO = True
CONFIG.app.SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_TEST}'


def load_sample_data():
    engine = create_engine(CONFIG.app.SQLALCHEMY_DATABASE_URI, echo=CONFIG.app.SQLALCHEMY_ECHO)
    with engine.connect() as conn, open(SAMPLE_DATA) as f:
        for statement in f.read().split(';'):
            conn.execute(execute_sql(statement))


EXTRAS = dict(
    conf=CONFIG.app,
    template_folder="blueprints/web/templates",
    static_folder="blueprints/web/static",
    callback=load_sample_data
)


@pytest.fixture(scope='session')
def test_client():
    try:
        os.remove(DB_TEST)
    except OSError as exc:
        print(str(exc))

    return TestClient.get_app(**{**APP_CONFIG, **EXTRAS}).test_client()


@pytest.fixture()
def auth_token(test_client):
    def get_access_token(token=None):
        if token is not None:
            return dict(Authorization=f"Bearer {token}")

        credentials = dict(email=h.config.ADMIN_EMAIL, password=h.config.ADMIN_PASSWORD)
        tokens = test_client.post(h.url_for(h.VIEWS.access_token), json=credentials)
        return dict(Authorization=f"Bearer {tokens.json.access_token}")

    return get_access_token
