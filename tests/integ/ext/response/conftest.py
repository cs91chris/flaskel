import flask
import pytest

from flaskel.ext.response.builder import ResponseBuilder


# pylint: disable=too-many-locals
@pytest.fixture
def app():
    _app = flask.Flask(__name__)
    _app.config["RB_HTML_DEFAULT_TEMPLATE"] = "response.html"
    rb = ResponseBuilder(_app)

    data = {
        "users": [
            {"id": 1, "name": "name-1"},
            {"id": 2, "name": "name-2"},
            {"id": 3, "name": "name-3"},
        ]
    }

    @_app.route("/json")
    @rb.json()
    def index_json():
        return data

    @_app.route("/xml")
    @rb.xml()
    def index_xml():
        return data

    @_app.route("/yaml")
    @rb.yaml()
    def index_yaml():
        return data

    @_app.route("/html")
    def index_html():
        builder = rb.html(name="Users", as_table=True)
        return builder(data=data["users"])

    @_app.route("/csv")
    def index_csv():
        builder = rb.csv(filename="users")
        return builder(data=data["users"])

    @_app.route("/base64")
    @rb.base64()
    def index_base64():
        return data

    @_app.route("/nocontent")
    @rb.no_content
    def nocontent():
        return

    @_app.route("/nocontent/custom")
    @rb.no_content
    def nocontent_custom():
        return None, 202

    @_app.route("/nocontent/error")
    @rb.no_content
    def nocontent_error():
        return data, 500, {"header": "header"}

    @_app.route("/xhr")
    @rb.template_or_json("response.html")
    def test_xhr():
        return data["users"]

    @_app.route("/onaccept")
    @rb.on_accept()
    def test_accept():
        return data["users"]

    @_app.route("/onacceptonly")
    @rb.on_accept(acceptable=["application/xml"])
    def test_acceptonly():
        return data["users"]

    @_app.route("/customaccept")
    def test_customaccept():
        _, builder = rb.get_mimetype_accept()
        return rb.build_response(builder, (data["users"][0], 206, {"header": "header"}))

    @_app.route("/format")
    @rb.on_format()
    def test_format():
        return data["users"]

    @_app.route("/decorator")
    @rb.response("json")
    def test_decorator():
        return data["users"], {"header": "header"}, 206

    @_app.route("/custom/mimetype")
    @rb.response("json")
    def custom_mimetype():
        return data["users"], {"Content-Type": "application/custom+json"}

    @_app.route("/custom/jsonp")
    @rb.response("json")
    def custom_jsonp():
        return {"pippo": 1, "pluto": 2}

    _app.testing = True
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client
