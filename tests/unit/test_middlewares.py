import pytest
from vbcore import uuid
from vbcore.datastruct import ObjectDict
from vbcore.tester.mixins import Asserter

from flaskel import middlewares


def test_base(flaskel_app, mock_wsgi_app):
    middle = middlewares.BaseMiddleware(mock_wsgi_app)
    Asserter.assert_equals(middle.get_config(), ObjectDict())

    middle = middlewares.BaseMiddleware(mock_wsgi_app)
    middle.flask_app = flaskel_app
    Asserter.assert_greater(len(middle.get_config()), 0)


def test_force_https(mock_wsgi_app):
    middle = middlewares.ForceHttps(mock_wsgi_app)
    environ = {}
    Asserter.assert_true(callable(middle(environ, mock_wsgi_app)))
    Asserter.assert_equals(environ["wsgi.url_scheme"], "https")


@pytest.mark.parametrize(
    "from_key, value, method",
    [
        ("HTTP_X_HTTP_METHOD_OVERRIDE", "FETCH", "FETCH"),
        ("QUERY_STRING", "_method_override=PATCH", "PATCH"),
    ],
    ids=[
        "from-header",
        "from-query-string",
    ],
)
def test_http_method_override(flaskel_app, mock_wsgi_app, from_key, value, method):
    middle = middlewares.HTTPMethodOverride(mock_wsgi_app)
    middle.flask_app = flaskel_app
    environ = {
        "REQUEST_METHOD": "POST",
        from_key: value,
    }
    Asserter.assert_true(callable(middle(environ, mock_wsgi_app)))
    Asserter.assert_equals(environ["REQUEST_METHOD"], method)


def test_request_id_missing(flaskel_app, mock_wsgi_app):
    middle = middlewares.RequestID(mock_wsgi_app)
    app = flaskel_app
    middle.flask_app = app
    app.config["REQUEST_ID_HEADER"] = "X-Request-ID"

    environ = {}
    Asserter.assert_true(callable(middle(environ, mock_wsgi_app)))
    Asserter.assert_true(isinstance(environ["HTTP_X_REQUEST_ID"], str))


def test_request_id_given(flaskel_app, mock_wsgi_app):
    middle = middlewares.RequestID(mock_wsgi_app)
    app = flaskel_app
    middle.flask_app = app
    app.config["REQUEST_ID_HEADER"] = "X-Request-ID"

    environ = {"HTTP_X_REQUEST_ID": uuid.get_uuid()}
    Asserter.assert_true(callable(middle(environ, mock_wsgi_app)))
    Asserter.assert_true(isinstance(environ["HTTP_X_REQUEST_ID"], str))


def test_request_id_prefixed(flaskel_app, mock_wsgi_app):
    middle = middlewares.RequestID(mock_wsgi_app)
    app = flaskel_app
    middle.flask_app = app
    app.config["REQUEST_ID_PREFIX"] = "PREFIX_"

    environ = {"HTTP_X_REQUEST_ID": "PREFIX_123456"}
    Asserter.assert_true(callable(middle(environ, mock_wsgi_app)))
    Asserter.assert_true(isinstance(environ["HTTP_X_REQUEST_ID"], str))
