import base64
from unittest.mock import patch

import pytest
from vbcore.http import httpcode, HttpMethod
from vbcore.tester.mixins import Asserter
from werkzeug.datastructures import Headers

import flaskel
from flaskel.ext.default import caching


@pytest.mark.parametrize(
    "key, expected",
    [
        ("value", "value"),
        (lambda: "value", "value"),
    ],
    ids=["simple", "callable"],
)
def test_optional_callable(key, expected):
    Asserter.assert_equals(caching.optional_callable(key), expected)


def test_hash_method():
    data = "sample"
    hashed = caching.hash_method(data)
    Asserter.assert_equals(data, base64.b64decode(hashed).decode())


@pytest.mark.parametrize(
    "query_string, expected",
    [
        ("a=1&b=2", "a=1&b=2"),
        ("c=4&a=1&b=2&a=3", "a=1&a=3&b=2&c=4"),
        ("", ""),
    ],
    ids=["simple", "multi", "empty"],
)
def test_make_query_string(flaskel_app, query_string, expected):
    with flaskel_app.test_request_context(f"/?{query_string}"):
        query = caching.make_query_string()
        Asserter.assert_equals(query, expected)


@pytest.mark.parametrize(
    "headers, expected",
    [
        (Headers([("b", "b1"), ("a", "a1")]), "a1/b1"),
        (Headers([("a", "a1"), ("a", "a2")]), "a1/a2"),
        ({}, ""),
    ],
    ids=["simple", "multi", "empty"],
)
def test_make_headers_string(flaskel_app, headers, expected):
    with flaskel_app.test_request_context(headers=headers):
        query = caching.make_headers_string(["a", "b"], "/")
        Asserter.assert_equals(query, expected)


@pytest.mark.parametrize(
    "disabled, headers, expected",
    [
        (True, None, True),
        (False, None, False),
        (True, {"Cache-Control": caching.cache_control_bypass}, True),
        (False, {"Cache-Control": caching.cache_control_bypass}, True),
    ],
    ids=[
        "cache-disabled",
        "can-be-cached",
        "disabled-ignore-header",
        "bypassed-by-header",
    ],
)
def test_unless(flaskel_app, disabled, headers, expected):
    flaskel_app.config.CACHE_DISABLED = disabled
    with flaskel_app.test_request_context(headers=headers):
        Asserter.assert_equals(caching.unless(), expected)


@pytest.mark.parametrize(
    "method, status, expected",
    [
        (HttpMethod.GET, httpcode.SUCCESS, True),
        (HttpMethod.POST, httpcode.SUCCESS, False),
        (HttpMethod.GET, httpcode.BAD_REQUEST, False),
        (HttpMethod.GET, None, False),
    ],
    ids=[
        "can-be-cached",
        "method-not-allowed",
        "status-not-allowed",
        "unknown-respone",
    ],
)
def test_response_filter(flaskel_app, method, status, expected):
    with flaskel_app.test_request_context(method=method):
        response = {}
        if status is not None:
            response = flaskel.Response(status=status)
        filtered = caching.response_filter(response)
        Asserter.assert_equals(filtered, expected)


def test_make_cache_key(flaskel_app):
    query = "a=1&b=2"
    sep = caching.key_separator
    cts = f"hdr1{sep}hdr2"
    sample_header = "X-Hdr"
    headers = Headers([(sample_header, "hdr2"), (sample_header, "hdr1")])
    expected = f"{caching.key_prefix}/http://localhost{sep}{query}{sep}{cts}"

    obj = "flaskel.ext.default.caching"
    with patch(f"{obj}.hash_method") as mock_hash_method:
        with patch(f"{obj}.headers_in_keys") as mock_headers_in_keys:
            mock_hash_method.side_effect = lambda x: x
            mock_headers_in_keys.return_value = (sample_header,)
            with flaskel_app.test_request_context(f"/?{query}", headers=headers):
                Asserter.assert_equals(caching.make_cache_key(), expected)
                mock_hash_method.assert_called_once_with(f"{query}{sep}{cts}")


def test_cached(flaskel_app):
    response = "hello"

    def superclass_cached(**__):
        def wrapped(f, *args, **kwargs):
            return f(*args, **kwargs)

        return wrapped

    @caching.cached(source_check=True)
    def func_view(name):
        return f"{response} {name}"

    with patch("flaskel.ext.default.caching.superclass_cached") as mock_super:
        mock_super.side_effect = superclass_cached
        with flaskel_app.test_request_context():
            name_param = "world"
            Asserter.assert_equals(func_view(name_param), f"{response} {name_param}")

        mock_super.assert_called_once_with(
            unless=caching.unless,
            timeout=caching.default_timeout,
            make_cache_key=caching.make_cache_key,
            response_filter=caching.response_filter,
            source_check=True,
        )
