from flaskel.ext.response.notations import Case


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
