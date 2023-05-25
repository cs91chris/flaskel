import pytest
from vbcore import uuid
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.asserter import Asserter

from flaskel import cap
from flaskel.tester.helpers import ApiTester, config


def after_request_hook(response):
    cap.logger.info("AFTER_REQUEST_HOOK")
    return response


def before_request_hook():
    cap.logger.info("BEFORE_REQUEST_HOOK")


@pytest.mark.parametrize(
    "url, subdomain, content_type",
    [
        ("/", None, ContentTypeEnum.HTML),
        ("/", "api", ContentTypeEnum.JSON_PROBLEM),
        ("/", None, ContentTypeEnum.HTML),
        ("/webapp", None, ContentTypeEnum.HTML),
    ],
    ids=[
        "app",
        "api",
        "web",
        "spa",
    ],
)
def test_base_blueprints(url, subdomain, content_type, testapp, caplog):
    app = testapp(
        after_request=(after_request_hook,),
        before_request=(before_request_hook,),
    )
    client = ApiTester(app.test_client())

    response = client.get(
        url=url,
        subdomain=subdomain,
        status=httpcode.NOT_FOUND,
        mimetype=content_type,
    )

    Asserter.assert_true(uuid.check_uuid(response.headers[HeaderEnum.X_REQUEST_ID]))
    Asserter.assert_equals(caplog.records[-3].getMessage(), "BEFORE_REQUEST_HOOK")
    Asserter.assert_equals(caplog.records[-2].getMessage(), "AFTER_REQUEST_HOOK")


def test_api_cors(testapp):
    client = ApiTester(testapp().test_client())
    response = client.get("/", status=httpcode.NOT_FOUND)

    Asserter.assert_header(response, HeaderEnum.ACCESS_CONTROL_ALLOW_ORIGIN, "*")
    Asserter.assert_allin(
        response.headers[HeaderEnum.ACCESS_CONTROL_EXPOSE_HEADERS].split(", "),
        config.CORS_EXPOSE_HEADERS,
    )
