# pylint: disable=redefined-outer-name

import os

import pytest

from flaskel import middlewares, ObjectDict, TestClient
from flaskel.ext import (
    auth,
    builder,
    caching,
    cfremote,
    client_redis,
    cors,
    date_helper,
    errors,
    limit,
    logger,
    scheduler,
    sendmail,
    template,
    useragent,
    mongodb,
)
from flaskel.ext.crypto import argon2
from flaskel.ext.healthcheck import checks, health_checks
from flaskel.ext.sqlalchemy import db as sqlalchemy
from flaskel.extra.mobile_support import mobile_version, RedisStore
from flaskel.extra.stripe import payment_handler
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS, Fields
from flaskel.utils.schemas.openapi3 import SCHEMA as OPENAPI_SCHEMA
from .blueprints import BLUEPRINTS, VIEWS

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
SKEL_DIR = os.path.join(BASE_DIR, "skeleton")
CONF_DIR = os.path.join(SKEL_DIR, "res")

CTS = ObjectDict(
    text="text/plain",
    json="application/json",
    xml="application/xml",
    html="text/html",
    json_problem="application/problem+json",
    xml_problem="application/problem+xml",
    json_health="application/health+json",
)

HOSTS = ObjectDict(apitester="http://httpbin.org", fake="http://localhost")

SCHEMAS = dict(
    JSONRPC=DEFAULT_SCHEMAS.JSONRPC,
    API_PROBLEM=DEFAULT_SCHEMAS.API_PROBLEM,
    HEALTHCHECK=DEFAULT_SCHEMAS.HEALTH_CHECK,
    OPENAPI3=OPENAPI_SCHEMA,
    ITEM_POST=Fields.object(properties={"item": Fields.string}),
    ITEM=Fields.object(properties={"id": Fields.integer, "item": Fields.string}),
    ITEM_LIST=Fields.array_object(
        properties={"id": Fields.integer, "item": Fields.string}
    ),
)

BASE_EXTENSIONS = {
    # "name":   (<extension>, parameters: dict)
    "cfremote": (cfremote,),  # MUST be the first
    "logger": (logger,),  # MUST be the second
    "template": (template,),
    "builder": (builder,),
    "date_helper": (date_helper,),
    "cors": (cors,),
    "database": (sqlalchemy,),
    "limiter": (limit.limiter,),
    "ip_ban": (limit.ip_ban,),
    "cache": (caching,),
    "errors": (
        errors.error_handler,
        {
            "dispatcher": "subdomain",
            "response": builder.on_accept(strict=False),
            "normalizer": errors.ErrorNormalizer(),
        },
    ),
    "useragent": (useragent,),
    "argon2": (argon2,),
    "caching": (caching,),
    "scheduler": (scheduler,),
    "sendmail": (sendmail.client_mail,),
    "redis": (client_redis,),
    "mongo": (mongodb,),
    "health_checks": (health_checks,),
    "jwt": (auth.jwtm,),
    "ipban": (limit.ip_ban,),
    "mobile_version": (
        mobile_version,
        dict(
            store=RedisStore(client_redis),
        ),
    ),
}

APISPEC = {
    "info": {"version": None},
    "servers": [
        {"variables": {"context": {"default": None}, "host": {"default": None}}}
    ],
}

PROXIES = {
    "CONF": dict(
        host=HOSTS.apitester, url="/anything", headers={"k": "v"}, params={"k": "v"}
    )
}


@pytest.fixture(scope="session")
def app_prod():
    # noinspection PyUnusedLocal
    def test_health_true(**__):
        return True, None

    # noinspection PyUnusedLocal
    def test_health_false(**__):
        return False, "error"

    health_checks.register("system")(checks.health_system)
    health_checks.register("mongo", db=sqlalchemy)(checks.health_mongo)
    health_checks.register("redis", db=sqlalchemy)(checks.health_redis)
    health_checks.register("sqlalchemy", db=sqlalchemy)(checks.health_sqlalchemy)
    health_checks.register("services", conf_key="HEALTH_SERVICES")(
        checks.health_services
    )

    return TestClient.get_app(
        conf=dict(
            DEBUG=True,
            BASIC_AUTH_USERNAME="username",
            BASIC_AUTH_PASSWORD="password",
            USER_AGENT_AUTO_PARSE=True,
            PREFERRED_URL_SCHEME="https",
            SCHEMAS=SCHEMAS,
            USE_X_SENDFILE=True,
            APIDOCS_ENABLED=True,
            APISPEC=APISPEC,
            PROXIES=PROXIES,
            HEALTH_SERVICES={
                "apitester": {"endpoint": HOSTS.apitester, "uri": "/anything"},
                "fakeapi": {"endpoint": HOSTS.fake, "uri": "/fake"},
            },
        ),
        blueprints=BLUEPRINTS,
        extensions={
            **BASE_EXTENSIONS,
            **{
                "ipban": None,
                "health_checks": (
                    health_checks,
                    {
                        "extensions": (
                            {"func": test_health_true, "name": "health_true"},
                            {"func": test_health_false},
                        )
                    },
                ),
            },
        },
        middlewares=(
            middlewares.ForceHttps,
            middlewares.HTTPMethodOverride,
            middlewares.ReverseProxied,
            middlewares.RequestID,
        ),
        folders=["skeleton/blueprints/web/templates"],
        static_folder="skeleton/blueprints/web/static",
    )


@pytest.fixture(scope="session")
def app_dev():
    return TestClient.get_app(
        conf=dict(
            DEBUG=True,
            WSGI_WERKZEUG_LINT_ENABLED=True,
            WSGI_WERKZEUG_PROFILER_ENABLED=True,
            FLASK_ENV="development",
            JSONRPC_BATCH_MAX_REQUEST=2,
            SCHEMAS=SCHEMAS,
            PROXIES=PROXIES,
            STRIPE_SECRET_KEY="stripe_secret_key",
            STRIPE_PUBLIC_KEY="stripe_public_key",
            BASIC_AUTH_USERNAME="admin",
            BASIC_AUTH_PASSWORD="admin",
        ),
        blueprints=(
            *BLUEPRINTS,
            *(None,),  # NB: needed to complete coverage
            *((None,),),  # NB: needed to complete coverage
        ),
        extensions={
            **BASE_EXTENSIONS,
            "empty": (None, (None,)),  # NB: needed to complete coverage
            "ipban": (limit.ip_ban, dict(nuisances=dict(string=["/phpmyadmin"]))),
            "stripe": (payment_handler,),
        },
        views=VIEWS,
        folders=["skeleton/blueprints/web/templates"],
        static_folder="skeleton/blueprints/web/static",
        after_request=(lambda x: x, lambda x: x),
        before_request=(lambda: None, lambda: None),
        version="1.0.0",
    )


@pytest.fixture(scope="session")
def testapp(app_prod):
    return app_prod.test_client()
