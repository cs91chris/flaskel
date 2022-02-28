from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.helpers import basic_auth_header
from vbcore.tester.mixins import Asserter

from flaskel.tester.helpers import ApiTester, url_for


def test_app_runs(test_client):
    ApiTester(test_client).get(test_client, "/", status=httpcode.NOT_FOUND)


def test_cors_headers(test_client):
    client = ApiTester(test_client)
    headers = test_client.application.config.CORS_EXPOSE_HEADERS

    res = client.get(url="/", status=httpcode.NOT_FOUND)
    Asserter.assert_header(res, HeaderEnum.ACCESS_CONTROL_ALLOW_ORIGIN, "*")
    Asserter.assert_allin(
        res.headers[HeaderEnum.ACCESS_CONTROL_EXPOSE_HEADERS].split(", "), headers
    )


def test_apidoc(test_client, views):
    client = ApiTester(test_client)
    headers = basic_auth_header()

    res = client.get(url_for(views.apidocs), headers=headers)
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, ContentTypeEnum.HTML)

    res = client.get(url_for(views.api_spec), headers=headers)
    Asserter.assert_status_code(res)
    Asserter.assert_different(res.json, {})
    Asserter.assert_content_type(res, ContentTypeEnum.JSON)
