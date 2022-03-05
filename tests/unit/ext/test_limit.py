from unittest.mock import patch

import pytest
from vbcore.http import httpcode
from vbcore.tester.mixins import Asserter

from flaskel import Response
from flaskel.ext.limit import ipban, response_ok, response_ko, header_whitelist


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


def test_ipban_init(flaskel_app):
    obj = "flaskel.ext.limit.ipban"
    with patch(f"{obj}.add_whitelist"), patch(f"{obj}.load_nuisances"):
        ipban.init_app(flaskel_app)

    Asserter.assert_true(flaskel_app.config.IPBAN_ENABLED)
    Asserter.assert_equals(flaskel_app.config.IPBAN_STATUS_CODE, httpcode.FORBIDDEN)


def test_ipban_is_whitelisted(flaskel_app):
    ip = "127.0.0.1"
    with flaskel_app.test_request_context():
        ipban.add_whitelist(ip)
        Asserter.assert_true(ipban.is_whitelisted(ip))
        ipban.remove_whitelist(ip)
        Asserter.assert_false(ipban.is_whitelisted(ip))
        Asserter.assert_true(ipban.is_whitelisted(url="/robots.txt"))


def test_load_nuisances():
    loaded = ipban.load_nuisances(
        {
            "regex": [
                r".*\.aspx$",
                r".*\.php$",
                r".*\.py$",
                r".*\.sh$",
                r".*\.sql$",
                r"\/.*\/(calendar|date|fortune|redirect|passwd)$",
                r".*?PHPSESSID=",
                r"\/([sf]|web|ows|mp)cgi(-bin|)\/",
                r"^/\.git",
            ],
            "string": [
                "/index.php/admin/",
                "/joomla/",
                "/manager/html",
                "/myadmin/",
                "/mysqladmin/",
                "/phpmyadmin/",
                "/remote/login",
                "/temp/wp-admin/",
            ],
            "ip": [
                "8.8.8.8",
                "1.1.1.1",
                "2.2.2.2",
            ],
        }
    )

    Asserter.assert_equals(loaded, 20)
