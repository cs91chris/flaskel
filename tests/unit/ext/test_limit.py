import pytest
from vbcore.http import httpcode
from vbcore.tester.asserter import Asserter

from flaskel import Response
from flaskel.ext.limit import header_whitelist, response_ko, response_ok


@pytest.mark.parametrize(
    "status, expected",
    [
        (httpcode.SUCCESS, True),
        (httpcode.NO_CONTENT, True),
        (httpcode.BAD_REQUEST, False),
        (httpcode.INTERNAL_SERVER_ERROR, False),
    ],
)
def test_response_ok(status, expected):
    Asserter.assert_equals(response_ok(Response(status=status)), expected)


@pytest.mark.parametrize(
    "status, expected",
    [
        (httpcode.BAD_REQUEST, True),
        (httpcode.INTERNAL_SERVER_ERROR, True),
        (httpcode.SUCCESS, False),
        (httpcode.NO_CONTENT, False),
        (httpcode.TOO_MANY_REQUESTS, False),
    ],
)
def test_response_ko(status, expected):
    Asserter.assert_equals(response_ko(Response(status=status)), expected)


def test_bypass_limit(flaskel_app):
    with flaskel_app.test_request_context():
        Asserter.assert_false(header_whitelist())

    bypass_key, bypass_value = "X-Limiter-Bypass", "bypass-rate-limit"
    flaskel_app.config.LIMITER = {
        "BYPASS_KEY": bypass_key,
        "BYPASS_VALUE": bypass_value,
    }

    with flaskel_app.test_request_context(headers={bypass_key: bypass_value}):
        Asserter.assert_true(header_whitelist())
