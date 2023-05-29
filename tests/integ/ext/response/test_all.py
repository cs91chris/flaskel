import pytest
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.asserter import Asserter

from flaskel.tester.helpers import ApiTester


@pytest.mark.parametrize(
    "url, mimetype",
    [
        ("/html", ContentTypeEnum.HTML),
        ("/json", ContentTypeEnum.JSON),
        ("/xml", ContentTypeEnum.XML),
        ("/csv", ContentTypeEnum.CSV),
        ("/yaml", "application/yaml"),
        ("/base64", "application/base64"),
        ("/json?callback=pippo", "application/javascript"),
    ],
)
def test_app_returns_correct_content_type(client, url, mimetype):
    ApiTester(client).get(url=url, mimetype=mimetype)


def test_no_content(client):
    res = ApiTester(client).get(url="/nocontent", status=httpcode.NO_CONTENT)
    Asserter.assert_not_in("Content-Type", res.headers)
    Asserter.assert_not_in("Content-Length", res.headers)


def test_no_content_custom(client):
    res = ApiTester(client).get(url="/nocontent/custom", status=httpcode.ACCEPTED)
    Asserter.assert_not_in("Content-Type", res.headers)
    Asserter.assert_equals(res.headers["Content-Length"], "0")


def test_no_content_error(client):
    res = ApiTester(client).get(
        url="/nocontent/error", status=httpcode.INTERNAL_SERVER_ERROR
    )
    Asserter.assert_equals(res.headers.get("header"), "header")


def test_on_format_default(client):
    ApiTester(client).get(url="/format", mimetype=ContentTypeEnum.JSON)


@pytest.mark.parametrize(
    "fmt, mimetype",
    [
        ("html", ContentTypeEnum.HTML),
        ("json", ContentTypeEnum.JSON),
        ("xml", ContentTypeEnum.XML),
        ("csv", ContentTypeEnum.CSV),
        ("yaml", "application/yaml"),
        ("base64", "application/base64"),
    ],
)
def test_on_format(client, fmt, mimetype):
    ApiTester(client).get(url=f"/format?format={fmt}", mimetype=mimetype)


def test_on_accept_default(client):
    ApiTester(client).get(
        url="/onaccept", headers={"Accept": "*/*"}, mimetype=ContentTypeEnum.JSON
    )


@pytest.mark.parametrize(
    "mimetype",
    [
        ContentTypeEnum.HTML,
        ContentTypeEnum.JSON,
        ContentTypeEnum.XML,
        ContentTypeEnum.CSV,
        "application/yaml",
        "application/base64",
    ],
)
def test_on_accept(client, mimetype):
    ApiTester(client).get(
        url="/onaccept", headers={"Accept": mimetype}, mimetype=mimetype
    )


def test_on_accept_multiple(client):
    ApiTester(client).get(
        url="/onaccept",
        headers={"Accept": "application/xml;encoding=utf-8;q=0.8, text/csv;q=0.4"},
        mimetype=ContentTypeEnum.XML,
    )


def test_on_accept_error(client):
    ApiTester(client).get(
        url="/onaccept",
        headers={"Accept": "custom/format"},
        status=httpcode.NOT_ACCEPTABLE,
    )


def test_on_accept_only(client):
    tester = ApiTester(client)
    tester.get(
        url="/onacceptonly",
        headers={"Accept": ContentTypeEnum.XML},
        mimetype=ContentTypeEnum.XML,
    )
    tester.get(
        url="/onacceptonly",
        headers={"Accept": ContentTypeEnum.JSON},
        status=httpcode.NOT_ACCEPTABLE,
    )


def test_custom_accept(client):
    res = ApiTester(client).get(
        url="/customaccept",
        headers={"Accept": ContentTypeEnum.XML},
        mimetype=ContentTypeEnum.XML,
        status=httpcode.PARTIAL_CONTENT,
    )
    Asserter.assert_equals(res.headers["header"], "header")


def test_template_or_json(client):
    tester = ApiTester(client)
    tester.get(url="/xhr", mimetype=ContentTypeEnum.JSON)
    tester.get(
        url="/xhr",
        headers={"X-Requested-With": "XMLHttpRequest"},
        mimetype=ContentTypeEnum.HTML,
    )


def test_response_decorator(client):
    res = ApiTester(client).get(
        url="/decorator", mimetype=ContentTypeEnum.JSON, status=httpcode.PARTIAL_CONTENT
    )
    Asserter.assert_equals(res.headers["header"], "header")


def test_custom_mimetype(client):
    ApiTester(client).get(url="/custom/mimetype", mimetype="application/custom+json")


def test_jsonp(client):
    res = ApiTester(client).get(
        url="/custom/jsonp?callback=pippo", mimetype="application/javascript"
    )
    data = res.data.decode()
    Asserter.assert_true(data.startswith("pippo("))
    Asserter.assert_true(data.endswith(");"))
