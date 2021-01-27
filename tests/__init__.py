import os

import pytest

from flaskel import datastruct, middlewares
from flaskel.ext import BASE_EXTENSIONS, crypto, healthcheck, sqlalchemy, useragent
from flaskel.ext.auth import jwtm
from flaskel.tester import TestClient
from tests.blueprints import BLUEPRINTS

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
SKEL_DIR = os.path.join(BASE_DIR, 'skeleton')
CONF_DIR = os.path.join(SKEL_DIR, 'config')

CTS = datastruct.ObjectDict(
    json='application/json',
    xml='application/xml',
    html='text/html',
    json_problem='application/problem+json',
    xml_problem='application/problem+xml',
    json_health='application/health+json',
)

HOSTS = datastruct.ObjectDict(
    apitester="http://httpbin.org",
    fake="http://localhost"
)


@pytest.fixture(scope='session')
def app_prod():
    # noinspection PyUnusedLocal
    def test_health_true(**kwargs):
        return True, None

    # noinspection PyUnusedLocal
    def test_health_false(**kwargs):
        return False, "error"

    healthcheck.health_checks.register('system')(healthcheck.health_system)
    healthcheck.health_checks.register('mongo', db=sqlalchemy.db)(healthcheck.health_mongo)
    healthcheck.health_checks.register('redis', db=sqlalchemy.db)(healthcheck.health_redis)
    healthcheck.health_checks.register('sqlalchemy', db=sqlalchemy.db)(healthcheck.health_sqlalchemy)

    return TestClient.get_app(
        conf=dict(
            DEBUG=True,
            BASIC_AUTH_USERNAME='username',
            BASIC_AUTH_PASSWORD='password',
            USER_AGENT_AUTO_PARSE=True,
            PREFERRED_URL_SCHEME='https',
            PROXIES=dict(
                CONF=dict(
                    host=HOSTS.apitester,
                    url='/anything',
                    headers={'k': 'v'},
                    params={'k': 'v'}
                )
            )
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
                "jwt":           (jwtm,),
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


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='session')
def testapp(app_prod):
    return app_prod.test_client()
