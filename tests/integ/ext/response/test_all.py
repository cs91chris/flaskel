import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

import flask
import pytest

from flaskel.ext.response.builder import ResponseBuilder
from flaskel.ext.response.builders import CsvBuilder, JsonBuilder
from flaskel.ext.response.dictutils import rename_keys
from flaskel.ext.response.notations import Case
from flaskel.ext.response.transformations import Transformer


@pytest.fixture
def app():
    _app = flask.Flask(__name__)
    _app.config["RB_HTML_DEFAULT_TEMPLATE"] = "response.html"
    rb = ResponseBuilder(_app)

    data = {
        "users": [
            {
                "id": 1,
                "name": "Leanne Graham",
                "email": "Sincere@april.biz",
                "phone": "1-770-736-8031 x56442",
                "sysdate": datetime.now(),
                "address": {
                    "city": "Gwenborough",
                    "zipcode": "92998-3874",
                    "geo": {"lat": -37.3159, "lon": 81.1496},
                },
                "test": [
                    {"a": 1, "b": 2},
                    {"a": 2, "b": 3},
                ],
            },
            {
                "id": 2,
                "name": "Ervin Howell",
                "email": "Shanna@melissa.tv",
                "phone": "010-692-6593 x09125",
                "sysdate": datetime.now(),
                "address": {
                    "city": "Wisokyburgh",
                    "zipcode": "90566-7771",
                    "geo": {"lat": -43.9509, "lon": -34.4618},
                },
                "test": [{"a": None, "b": None}],
            },
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
        item = flask.request.args.get("item")
        if item is not None:
            try:
                return data["users"][int(item)]
            except IndexError:
                return []
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
        old = datetime.now()

        class Color(Enum):
            red = "red"
            green = "green"
            blue = "blue"

        resp = {
            "id": uuid.uuid4(),
            "name": "Leanne Graham",
            "email": "Sincere@april.biz",
            "sysdate": datetime.now(),
            "time": datetime.now().time(),
            "date": datetime.now().date(),
            "delta": old - datetime.now(),
            "color": Color.red,
            "address": {
                "city": "Gwenborough",
                "zipcode": "92998-3874",
                "geo": {"lat": Decimal(-37.3159), "lon": Decimal(81.1496)},
            },
        }
        resp.pop("sysdate")
        return resp, {"header": "header"}, 206

    @_app.route("/rename-key")
    @rb.response("json")
    def rename_key():
        return rename_keys({"pippo": 1, "pluto": 2}, trans=str.upper)

    @_app.route("/notation")
    @rb.response("json")
    def notation():
        word = "pippo pluto"
        return [word, Case.to_camel(word), Case.to_kebab(word), Case.to_snake(word)]

    @_app.route("/json2xml", methods=["POST"])
    def json_to_xml():
        return flask.Response(Transformer.json_to_xml(flask.request.data))

    @_app.route("/json2csv", methods=["POST"])
    def json_to_csv():
        return flask.Response(Transformer.json_to_csv(flask.request.data))

    @_app.route("/json2yaml", methods=["POST"])
    def json_to_yaml():
        return flask.Response(Transformer.json_to_yaml(flask.request.data))

    @_app.route("/transform")
    def test_transform():
        b = JsonBuilder(mimetype="application/json")
        return flask.Response(
            b.transform('"pippo";"pluto"\r\n"2";"3"\r\n', builder=CsvBuilder),
            headers={"Content-Type": b.mimetype},
        )

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


def test_app_runs(client):
    res = client.get("/")
    assert res.status_code == 404


def test_app_returns_correct_content_type(client):
    res = client.get("/html")
    assert res.status_code == 200
    assert "text/html" in res.headers["Content-Type"]

    res = client.get("/json")
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]

    res = client.get("/json?callback=pippo")
    assert res.status_code == 200
    assert "application/javascript" in res.headers["Content-Type"]

    res = client.get("/xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers["Content-Type"]

    res = client.get("/yaml")
    assert res.status_code == 200
    assert "application/yaml" in res.headers["Content-Type"]

    res = client.get("/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]

    res = client.get("/base64")
    assert res.status_code == 200
    assert "application/base64" in res.headers["Content-Type"]


def test_no_content(client):
    res = client.get("/nocontent")
    assert res.status_code == 204
    # assert res.headers.get('Content-Type') is None TODO client seems add it
    # assert res.headers.get('Content-Length') == 0 TODO client seems remove it

    res = client.get("/nocontent/custom")
    assert res.status_code == 202
    # assert res.headers.get('Content-Type') is None TODO client seems add it
    # assert res.headers.get('Content-Length') == 0 TODO client seems remove it


def test_no_content_error(client):
    res = client.get("/nocontent/error")
    assert res.status_code == 500
    assert res.headers.get("header") == "header"


def test_on_format(client):
    res = client.get("/format?format=xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers["Content-Type"]

    res = client.get("/format?format=yaml")
    assert res.status_code == 200
    assert "application/yaml" in res.headers["Content-Type"]

    res = client.get("/format")
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]


def test_on_accept(client):
    res = client.get("/onaccept", headers={"Accept": "*/*"})
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]

    res = client.get("/onaccept?item=11111", headers={"Accept": "*/*"})
    assert res.status_code == 200
    assert len(res.get_json()) == 0

    res = client.get(
        "/onaccept",
        headers={"Accept": "application/xml;encoding=utf-8;q=0.8, text/csv;q=0.4"},
    )
    assert res.status_code == 200
    assert "application/xml" in res.headers["Content-Type"]

    res = client.get("/onaccept", headers={"Accept": "text/csv"})
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]

    res = client.get("/onaccept", headers={"Accept": "custom/format"})
    assert res.status_code == 406


def test_on_accept_only(client):
    res = client.get("/onacceptonly", headers={"Accept": "application/xml"})
    assert res.status_code == 200
    assert "application/xml" in res.headers["Content-Type"]

    res = client.get("/onacceptonly", headers={"Accept": "application/json"})
    assert res.status_code == 406


def test_custom_accept(client):
    res = client.get("/customaccept", headers={"Accept": "application/xml"})
    assert res.status_code == 206
    assert "application/xml" in res.headers["Content-Type"]
    assert res.headers["header"] == "header"


def test_template_or_json(client):
    res = client.get("/xhr")
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]

    res = client.get("/xhr", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 200
    assert "text/html" in res.headers["Content-Type"]


def test_response_decorator(client):
    res = client.get("/decorator")
    assert res.status_code == 206
    assert "application/json" in res.headers["Content-Type"]
    assert res.headers["header"] == "header"


def test_rename_key(client):
    res = client.get("/rename-key")
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]

    data = res.get_json()
    assert data["PIPPO"] == 1
    assert data["PLUTO"] == 2


def test_notation(client):
    res = client.get("/notation")
    assert res.status_code == 200

    data = res.get_json()
    assert Case.are_words(data[0])
    assert Case.is_camel(data[1])
    assert Case.is_kebab(data[2])
    assert Case.is_snake(data[3])


def test_transformer(client):
    res = client.post("/json2xml", json={"pippo": 2, "pluto": 3})
    assert res.status_code == 200
    assert (
        res.data == b'<?xml version="1.0" encoding="UTF-8" ?>'
        b'<root><pippo type="int">2</pippo><pluto type="int">3</pluto></root>'
    )

    res = client.post("/json2csv", json=[{"pippo": 2, "pluto": 3}])
    assert res.status_code == 200
    assert res.data == b'"pippo";"pluto"\r\n"2";"3"\r\n'

    res = client.post("/json2yaml", json={"pippo": 2, "pluto": 3})
    assert res.status_code == 200
    assert res.data == b"pippo: 2\npluto: 3\n"


def test_build_transform(client):
    res = client.get("/transform")
    assert res.status_code == 200

    data = res.get_json()[0]
    assert data["pippo"] == "2"
    assert data["pluto"] == "3"


def test_custom_mimetype(client):
    res = client.get("/custom/mimetype")
    assert res.status_code == 200
    assert "application/custom+json" in res.headers["Content-Type"]


def test_jsonp(client):
    res = client.get("/custom/jsonp?callback=pippo")
    assert res.status_code == 200
    assert "application/javascript" in res.headers["Content-Type"]
    data = res.data.decode()
    assert data.startswith("pippo(") and data.endswith(");")
