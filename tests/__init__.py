import os

import pytest
from flask.testing import FlaskClient

from flaskel import AppFactory, middlewares
from flaskel.ext import BASE_EXTENSIONS, crypto, healthcheck, sqlalchemy, useragent
from tests.blueprints import BLUEPRINTS

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
SKEL_DIR = os.path.join(BASE_DIR, 'skeleton')
CONF_DIR = os.path.join(SKEL_DIR, 'config')


class TestClient(FlaskClient):
    """
        Implement this to customize Flask client
        Form example:
                def fetch(self, url, *args, **kwargs):
                    return self.open(url, method='FETCH', *args, **kwargs)
    """


@pytest.fixture
def app_prod():
    def test_health_true(**kwargs):
        return True, None

    def test_health_false(**kwargs):
        return False, "error"

    extra_ext = {
        "empty":         (None, (None,)),  # NB: needed to complete coverage
        "useragent":     (useragent.UserAgent(),),
        "argon2":        (crypto.Argon2(),),
        "health_checks": (healthcheck.health_checks, {'extensions': (
            {
                'name': 'health_true',
                'func': test_health_true,
            },
            {
                'func': test_health_false,
            },
        )},),
    }

    healthcheck.health_checks.register('mongo', db=sqlalchemy.db)(healthcheck.health_mongo)
    healthcheck.health_checks.register('redis', db=sqlalchemy.db)(healthcheck.health_redis)
    healthcheck.health_checks.register('sqlalchemy', db=sqlalchemy.db)(healthcheck.health_sqlalchemy)

    _app = AppFactory(
        blueprints=(*BLUEPRINTS, *(None,), *((None,),)),  # NB: needed to complete coverage
        extensions={**BASE_EXTENSIONS, **extra_ext},
        middlewares=(middlewares.ForceHttps, middlewares.HTTPMethodOverride, middlewares.ReverseProxied),
        folders=["skeleton/blueprints/web/templates"],
        static_folder="skeleton/blueprints/web/static"
    ).get_or_create(dict(TESTING=True))

    _app.test_client_class = TestClient
    _app.config.USER_AGENT_AUTO_PARSE = True
    return _app


@pytest.fixture
def app_dev():
    _app = AppFactory(
        blueprints=BLUEPRINTS,
        extensions=BASE_EXTENSIONS,
        template_folder="skeleton/blueprints/web/templates",
        static_folder="skeleton/blueprints/web/static"
    ).get_or_create(
        dict(DEBUG=True, FLASK_ENV='development')
    )

    _app.test_client_class = TestClient
    return _app


@pytest.fixture
def testapp(app_prod):
    return app_prod.test_client()
