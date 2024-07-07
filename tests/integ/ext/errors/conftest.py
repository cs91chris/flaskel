from datetime import datetime

import pytest
from flask import abort, Blueprint, Response
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.routing import RequestRedirect

from flaskel import config, Flaskel
from flaskel.ext.errors.dispatchers import SubdomainDispatcher
from flaskel.ext.errors.handler import ErrorHandler


@pytest.fixture
def error_handler():
    return ErrorHandler()


@pytest.fixture
def app(error_handler):  # pytest: ignore=too-many-locals
    _app = Flaskel(__name__)
    _app.config.from_object(config)
    _app.config["ERROR_PAGE"] = "error.html"
    _app.config["SERVER_NAME"] = "flask.dev:5000"

    api = Blueprint("api", __name__)
    web = Blueprint("web", __name__, url_prefix="/web")
    custom = Blueprint("custom", __name__, subdomain="api", url_prefix="/custom")

    error_handler.init_app(_app, dispatcher="notfound")
    error_handler.init_app(_app, dispatcher=SubdomainDispatcher)
    error_handler.api_register(api)
    error_handler.web_register(web)
    error_handler.failure_register(_app)

    @_app.route("/not-allowed", methods=["GET"])
    def test_not_allowed():
        return "Not allowed"

    @error_handler.register(custom)
    def error_handler_callback(exc):
        return str(exc), 404, {"Content-Type": "text/html", "custom": "test"}

    @api.route("/api")
    def index():
        abort(500, "Error from app")

    @api.route("/api/unauthorized")
    def unauthorized():
        auth = WWWAuthenticate(auth_type="Basic", values={"realm": "realm-name"})
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
    with app.app_context():
        _client = app.test_client()
        yield _client
