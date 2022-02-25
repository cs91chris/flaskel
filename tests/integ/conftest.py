import pytest

from flaskel import TestClient
from .components import (
    BLUEPRINTS,
    MIDDLEWARES,
    CONVERTERS,
    AFTER_REQUEST,
    BEFORE_REQUEST,
    EXTENSIONS,
)
from .helpers import (
    prepare_config,
    after_create_hook,
)


@pytest.fixture()
def testapp():
    def _get_app(config=None, extensions=None, views=()):
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
            extensions=EXTENSIONS.update(extensions or {}),
            after_create_hook=after_create_hook,
        )

    return _get_app
