from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from flaskel import Flaskel

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment


@pytest.fixture
def flaskel_app() -> Flaskel:
    app = Flaskel(__name__)
    app.testing = True
    app.debug = True
    return app


@pytest.fixture
def mock_wsgi_app():
    def _mock_wsgi_app(environ: "WSGIEnvironment", start_response: "StartResponse"):
        _ = environ, start_response
        return MagicMock()

    return _mock_wsgi_app
