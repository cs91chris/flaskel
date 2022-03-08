import os

import pytest

from flaskel import TestClient, db_session
from .components import (
    BLUEPRINTS,
    MIDDLEWARES,
    CONVERTERS,
    AFTER_REQUEST,
    BEFORE_REQUEST,
    EXTENSIONS,
)
from .helpers import prepare_config, DB_TEST


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
            after_request=AFTER_REQUEST,
            before_request=BEFORE_REQUEST,
            extensions={**EXTENSIONS, **(extensions or {})},
            **kwargs,
        )

    return _get_app
