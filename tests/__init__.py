import os

import pytest

from flaskel import middlewares
from flaskel.ext import BASE_EXTENSIONS, crypto, healthcheck, sqlalchemy, useragent
from flaskel.tester import TestClient
from tests.blueprints import BLUEPRINTS

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
SKEL_DIR = os.path.join(BASE_DIR, 'skeleton')
CONF_DIR = os.path.join(SKEL_DIR, 'config')


@pytest.fixture
def app_prod():
    # noinspection PyUnusedLocal
    def test_health_true(**kwargs):
        return True, None

    # noinspection PyUnusedLocal
    def test_health_false(**kwargs):
        return False, "error"

    healthcheck.health_checks.register('mongo', db=sqlalchemy.db)(healthcheck.health_mongo)
    healthcheck.health_checks.register('redis', db=sqlalchemy.db)(healthcheck.health_redis)
    healthcheck.health_checks.register('sqlalchemy', db=sqlalchemy.db)(healthcheck.health_sqlalchemy)

    return TestClient.get_app(
        conf=dict(
            TESTING=True,
            USER_AGENT_AUTO_PARSE=True,
            PREFERRED_URL_SCHEME='https'
        ),
        blueprints=(
            *BLUEPRINTS,
            *(None,),  # NB: needed to complete coverage
            *((None,),)  # NB: needed to complete coverage
        ),
        extensions={
            **BASE_EXTENSIONS,
            **{
                "empty":         (None, (None,)),  # NB: needed to complete coverage
                "useragent":     (useragent.UserAgent(),),
                "argon2":        (crypto.Argon2(),),
                "health_checks": (
                    healthcheck.health_checks, {'extensions': (
                        {
                            'name': 'health_true',
                            'func': test_health_true,
                        },
                        {
                            'func': test_health_false,
                        },
                    )},
                ),
            }
        },
        middlewares=(
            middlewares.ForceHttps,
            middlewares.HTTPMethodOverride,
            middlewares.ReverseProxied,
            middlewares.RequestID,
        ),
        folders=["skeleton/blueprints/web/templates"],
        static_folder="skeleton/blueprints/web/static"
    )


@pytest.fixture
def app_dev():
    return TestClient.get_app(
        conf=dict(
            DEBUG=True,
            FLASK_ENV='development'
        ),
        blueprints=BLUEPRINTS,
        extensions=BASE_EXTENSIONS,
        template_folder="skeleton/blueprints/web/templates",
        static_folder="skeleton/blueprints/web/static"
    )


@pytest.fixture
def testapp(app_prod):
    return app_prod.test_client()
