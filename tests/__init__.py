import os

import pytest

from flaskel import datastruct, middlewares, tester
from flaskel.ext import (
    auth, BASE_EXTENSIONS, caching, crypto, healthcheck,
    ip_ban, jobs, limiter, sqlalchemy, useragent
)
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

SCHEMA_DIR = 'skeleton/blueprints/api/static/schemas'

SCHEMAS = dict(
    JSONRPC=f"file://{SCHEMA_DIR}/jsonrpc.json",
    APIPROBLEM=f"file://{SCHEMA_DIR}/apiproblem.json",
    HEALTHCHECK=f"file://{SCHEMA_DIR}/healthcheck.json",
    OPENAPI3=f"file://{SCHEMA_DIR}/openapi3.json",
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

    return tester.TestClient.get_app(
        conf=dict(
            DEBUG=True,
            BASIC_AUTH_USERNAME='username',
            BASIC_AUTH_PASSWORD='password',
            USER_AGENT_AUTO_PARSE=True,
            PREFERRED_URL_SCHEME='https',
            SCHEMAS=SCHEMAS,
            USE_X_SENDFILE=True,
            JSONRPC_BATCH_MAX_REQUEST=2,
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
                "jwt":           (auth.jwtm,),
                "limiter":       (limiter,),
                "caching":       (caching,),
                "sqlalchemy":    (sqlalchemy.db,),
                "scheduler":     (jobs.scheduler,),
                "ipban":         (ip_ban, dict(nuisances=dict(string=["/phpmyadmin"]))),
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
    return tester.TestClient.get_app(
        conf=dict(
            DEBUG=True,
            WSGI_WERKZEUG_LINT_ENABLED=True,
            WSGI_WERKZEUG_PROFILER_ENABLED=True,
            FLASK_ENV='development',
            SCHEMAS=SCHEMAS
        ),
        blueprints=BLUEPRINTS,
        extensions=BASE_EXTENSIONS,
        template_folder="skeleton/blueprints/web/templates",
        static_folder="skeleton/blueprints/web/static"
    )


@pytest.fixture(scope='session')
def testapp(app_prod):
    return app_prod.test_client()
