import os

import pytest
from vbcore import yaml
from vbcore.datastruct import ObjectDict

from flaskel import TestClient, db_session
from flaskel.converters import CONVERTERS
from flaskel.ext import default, auth
from flaskel.middlewares import RequestID, HTTPMethodOverride
from tests.integ.views import bp_api, bp_spa, bp_web

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "data")
DB_TEST = os.path.join(SAMPLE_DIR, "test.sqlite")

MIDDLEWARES = (
    RequestID,
    HTTPMethodOverride,
)
BLUEPRINTS = (
    (bp_api,),
    (bp_spa,),
    (bp_web,),
)

EXTENSIONS = {
    "cfremote": (default.cfremote,),
    "logger": (default.logger,),
    "argon2": (default.argon2,),
    "auth": (auth.token_auth,),
    "builder": (default.builder,),
    "cors": (default.cors, dict(resources={r"/*": {"origins": "*"}})),
    "database": (default.Database(),),
    "date_helper": (default.date_helper,),
    "errors": (
        default.error_handler,
        dict(
            dispatcher="subdomain",
            response=default.builder.on_accept(strict=False),
        ),
    ),
    "template": (default.template,),
    "useragent": (default.useragent,),
}


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


@pytest.fixture()
def session_save():
    def _save(items):
        for i in items:
            db_session.merge(i)
        db_session.commit()

    return _save


@pytest.fixture(scope="session")
def testapp():
    try:
        os.remove(DB_TEST)
    except OSError as exc:
        print(str(exc))

    def _get_app(config=None, extensions=None, views=(), **kwargs):
        return TestClient.get_app(
            version="1.0.0",
            static_folder=None,
            conf=prepare_config(config),
            views=views,
            blueprints=BLUEPRINTS,
            middlewares=MIDDLEWARES,
            converters=CONVERTERS,
            extensions={**EXTENSIONS, **(extensions or {})},
            **kwargs,
        )

    return _get_app
