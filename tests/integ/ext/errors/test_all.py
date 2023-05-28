from datetime import datetime

import pytest
from flask import abort, Blueprint, Flask, Response
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.routing import RequestRedirect

from flaskel.ext.errors.dispatchers import SubdomainDispatcher, URLPrefixDispatcher
from flaskel.ext.errors.handler import ErrorHandler

error = ErrorHandler()


@pytest.fixture
def app():
    _app = Flask(__name__)
    _app.config["ERROR_PAGE"] = "error.html"
    _app.config["SERVER_NAME"] = "flask.dev:5000"

    api = Blueprint("api", __name__)
    web = Blueprint("web", __name__, url_prefix="/web")
    custom = Blueprint("custom", __name__, subdomain="api", url_prefix="/custom")

    error.init_app(_app, dispatcher="notfound")
    error.init_app(_app, dispatcher=SubdomainDispatcher)
    error.api_register(api)
    error.web_register(web)
    error.failure_register(_app)

    @_app.route("/not-allowed", methods=["GET"])
    def test_not_allowed():
        return "Not allowed"

    @error.register(custom)
    def error_handler(exc):
        return str(exc), 404, {"Content-Type": "text/html", "custom": "test"}

    @api.route("/api")
    def index():
        abort(500, "Error from app")

    @api.route("/api/unauthorized")
    def unauthorized():
        auth = WWWAuthenticate(
            auth_type="Basic", values={"realm": "authentication required"}
        )
        abort(401, www_authenticate=auth)

    @api.route("/api/retry")
    def retry():
        abort(429, retry_after=datetime(year=2000, month=3, day=1))

    @api.route("/api/response")
    def response():
        abort(500, response=Response("response"))

    @api.route("/api/range")
    def ranger():
        abort(416, length=10)

    @api.route("/permanent/")
    def permanent():
        return "redirected"

    @api.route("/api/error")
    def api_error():
        raise NameError("exception from app")

    @api.route("/methodnotallowed/option")
    def method_not_allowed_option():
        abort(405, valid_methods=["GET", "POST"])

    @api.route("/methodnotallowed")
    def method_not_allowed_without_option():
        abort(405)

    @web.route("/web")
    def index_web():
        abort(500, "Error from web blueprint")

    @web.route("/redirect")
    def redirect():
        raise RequestRedirect("/web")

    @web.route("/web/error")
    def web_error():
        _app.config["ERROR_PAGE"] = None
        abort(500, "Error from web blueprint")

    @custom.route("/custom")
    def index_custom():
        abort(500, "Error from custom blueprint")

    _app.register_blueprint(api)
    _app.register_blueprint(custom, url_prefix="/custom")
    _app.register_blueprint(web, url_prefix="/web")

    _app.testing = True
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get("/")
    assert res.status_code == 404
    assert res.get_json()["type"] == "https://httpstatuses.com/404"


def test_method_not_allowed(client):
    res = client.post("/api")
    assert res.status_code == 405
    assert "Allow" in res.headers
    assert "allowed" in res.get_json()["response"]
    assert res.get_json()["type"] == "https://httpstatuses.com/405"


def test_api(client):
    res = client.get("/api")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"

    data = res.get_json()
    assert data["type"] == "https://httpstatuses.com/500"
    assert data["title"] == "Internal Server Error"
    assert data["detail"] is not None
    assert data["status"] == 500
    assert data["instance"] == "about:blank"
    assert data["response"] is None


def test_api_error(client):
    res = client.get("/api/error")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"


def test_web(client):
    res = client.get("/web/web")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"


def test_web_redirect(client):
    res = client.get("/web/redirect")
    assert res.status_code == 308
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"
    assert res.headers.get("Location").endswith("/web")


def test_web_xhr(client):
    res = client.get("/web/web", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"


def test_web_error(client):
    res = client.get("/web/web/error")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"


def method_not_allowed(client):
    res = client.get("/methodnotallowed")
    assert res.status_code == 405
    assert res.headers.get("Allow") is None

    res = client.get("/methodnotallowed/options")
    assert res.status_code == 405
    assert res.headers["Allow"] == "GET, POST"
    assert res.get_json()["response"]["Allow"] == ["GET", "POST"]


def test_custom(client, app):
    res = client.get(
        "/custom/custom", base_url="http://api." + app.config["SERVER_NAME"]
    )
    assert res.status_code == 404
    assert res.headers.get("Content-Type") == "text/html"


def test_dispatch_error_web(client, app):
    error.register_dispatcher(app, URLPrefixDispatcher)
    res = client.get("/web/web/page-not-found")
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]


def test_dispatch_error_api(client, app):
    res = client.get(
        "/api-not-found", base_url="http://api." + app.config["SERVER_NAME"]
    )
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]
    assert "test" in res.headers["custom"]


def test_dispatch_default(client, app):
    error.register_dispatcher(app, dispatcher="default")
    res = client.get("/not-found")
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]
    assert "https://httpstatuses.com/404" in res.data.decode()

    res = client.post("/not-allowed")
    assert res.status_code == 405
    assert "text/html" in res.headers["Content-Type"]
    assert "https://httpstatuses.com/405" in res.data.decode()


def test_permanent_redirect(client):
    res = client.get("/permanent")
    assert res.status_code in (301, 308)
    assert "Location" in res.headers


def test_response(client):
    res = client.get("/api/response")
    assert res.status_code == 500
    assert res.data == b"response"


def test_unauthorized(client):
    res = client.get("/api/unauthorized")
    assert res.status_code == 401
    assert res.headers["WWW-Authenticate"] == 'Basic realm="authentication required"'
    auth = res.get_json()["response"]["authenticate"][0]
    assert auth["auth_type"] == "basic"
    assert auth["realm"] == "authentication required"


def test_retry_after(client):
    date = "Wed, 01 Mar 2000 00:00:00 GMT"
    res = client.get("/api/retry")
    assert res.status_code == 429
    assert res.headers["Retry-After"] == date
    assert res.get_json()["response"]["retry_after"] == date


def test_range(client):
    res = client.get("/api/range")
    assert res.status_code == 416
    assert res.headers["Content-Range"] == "bytes */10"
    data = res.get_json()["response"]
    assert data["length"] == 10
    assert data["units"] == "bytes"
