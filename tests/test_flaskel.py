import json
import os
import time

import werkzeug.exceptions

from flaskel import misc, ObjectDict, uuid
from flaskel.http import (
    batch,
    FlaskelHttp,
    FlaskelJsonRPC,
    HTTPClient,
    HTTPStatusError,
    rpc,
    useragent,
)
from flaskel.tester import helpers as h
from flaskel.tester.http import TestHttpApi, TestHttpCall, TestJsonRPC, TestRestApi
from flaskel.utils import datetime, ExtProxy, schemas
from flaskel.utils.faker import DummyLogger

HOSTS = ObjectDict(
    apitester="http://httpbin.org",
    fake="http://localhost",
)


def test_app_dev(app_dev):
    h.Asserter.assert_equals(app_dev.config.FLASK_ENV, "development")
    h.Asserter.assert_equals(app_dev.config.SECRET_KEY, "fake_very_complex_string")

    client = TestHttpCall(app_dev.test_client())
    client.perform(request={"url": h.url_for("web.index")})

    client = TestHttpApi(app_dev.test_client())
    client.perform(request={"url": h.url_for("test.test_https")})
    h.Asserter.assert_equals(client.json.scheme, "https")
    h.Asserter.assert_true(client.json.url_for.startswith("https"))


def test_api_resources(testapp):
    res = testapp.get(h.url_for("api.resource_api"), headers={"Accept": h.CTS.xml})
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.xml)

    res = testapp.get(h.url_for("api.resource_api", res_id=1))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.json)

    res = testapp.get(h.url_for("api.resource_api", res_id=1, sub_resource="items"))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.json)

    res = testapp.get(h.url_for("api.resource_api", res_id=1, sub_resource="not-found"))
    h.Asserter.assert_status_code(res, h.httpcode.NOT_FOUND)
    h.Asserter.assert_content_type(res, h.CTS.json_problem)
    h.Asserter.assert_schema(res.json, schemas.SCHEMAS.API_PROBLEM)
    h.Asserter.assert_equals(res.json.detail, "not found")

    res = testapp.get(h.url_for("api.resource_api", res_id=1, sub_resource="not-found"))
    h.Asserter.assert_status_code(res, h.httpcode.TOO_MANY_REQUESTS)

    time.sleep(int(res.headers.get("Retry-After") or 0))  # check rate limit
    res = testapp.delete(h.url_for("api.resource_api", res_id=1))
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)

    data = dict(item="test")
    res = testapp.put(h.url_for("api.resource_api", res_id=1), json=data)
    h.Asserter.assert_status_code(res)

    res = testapp.post(h.url_for("api.resource_api"), json=data)
    h.Asserter.assert_status_code(res, h.httpcode.CREATED)

    res = testapp.post(
        h.url_for("api.resource_api", res_id=1, sub_resource="items"), json=data
    )
    h.Asserter.assert_status_code(res, h.httpcode.CREATED)

    res = testapp.post(h.url_for("api.resource_api"), json={})
    h.Asserter.assert_status_code(res, h.httpcode.UNPROCESSABLE_ENTITY)
    h.Asserter.assert_allin(res.json.response.reason, ("cause", "message", "path"))


def test_api_cors(testapp):
    client = TestHttpApi(testapp)
    client.perform(
        request={"url": h.url_for("api.resource_api")},
        response={
            "status": {"code": h.httpcode.TOO_MANY_REQUESTS},
            "headers": {
                "Access-Control-Allow-Origin": {"value": "*"},
                "Content-Type": {"value": h.CTS.json_problem},
            },
        },
    )

    headers = testapp.application.config.CORS_EXPOSE_HEADERS
    res = h.api_tester(testapp, url="/")
    h.Asserter.assert_header(res, "Access-Control-Allow-Origin", "*")
    h.Asserter.assert_allin(
        res.headers["Access-Control-Expose-Headers"].split(", "), headers
    )


def test_dispatch_error_web(testapp):
    client = TestHttpCall(testapp)
    client.perform(
        request={"url": "/web-page-not-found"},
        response={"status": {"code": h.httpcode.NOT_FOUND}},
    )


def test_dispatch_error_api(testapp):
    client = TestHttpApi(testapp)
    client.perform(
        request={
            "url": f"http://api.{testapp.application.config.SERVER_NAME}/not_found"
        },
        response={
            "status": {"code": h.httpcode.NOT_FOUND},
            "headers": {"Content-Type": {"value": h.CTS.json_problem}},
            "schema": schemas.SCHEMAS.API_PROBLEM,
        },
    )


def test_force_https(testapp):
    _ = testapp.get(h.url_for("test.test_https"))
    client = TestHttpApi(testapp)
    client.perform(request={"url": h.url_for("test.test_https")})
    h.Asserter.assert_equals(client.json.scheme, "https")
    h.Asserter.assert_true(client.json.url_for.startswith("https"))


def test_reverse_proxy(testapp):
    res = testapp.get(
        h.url_for("test.test_proxy"), headers={"X-Forwarded-Prefix": "/test"}
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_true(bool(res.json.request_id))
    h.Asserter.assert_equals(res.json.script_name, "/test")
    h.Asserter.assert_equals(res.json.original.SCRIPT_NAME, "")


def test_secret_key_prod(testapp):
    h.Asserter.assert_equals(testapp.application.config.FLASK_ENV, "production")
    h.Asserter.assert_true(os.path.isfile(".secret.key"))
    os.remove(".secret.key")


def test_method_override(testapp):
    res = testapp.post(
        h.url_for("test.method_override_post"),
        headers={"X-HTTP-Method-Override": h.HttpMethod.PUT},
    )
    h.Asserter.assert_status_code(res)

    res = testapp.post(h.url_for("test.method_override_post", _method_override="PUT"))
    h.Asserter.assert_status_code(res)


def test_converters(testapp):
    res = testapp.get(h.url_for("test.list_converter", data=["a", "b", "c"]))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json, 3)


def test_utils_get_json(testapp):
    res = testapp.post(h.url_for("test.get_invalid_json"))
    h.Asserter.assert_status_code(res, h.httpcode.BAD_REQUEST)


def test_utils_send_file(testapp):
    filename = "MANIFEST.in"
    url = h.url_for("test.download") + "?filename={}"

    res = testapp.get(url.format(filename))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_header(
        res, "Content-Disposition", f"attachment; filename={filename}"
    )
    h.Asserter.assert_header(res, "X-Accel-Redirect", f"./{filename}")
    h.Asserter.assert_true(res.headers.get("X-Sendfile").endswith(filename))
    h.Asserter.assert_equals(res.data, b"")

    res = testapp.get(url.format("nofile.txt"))
    h.Asserter.assert_status_code(res, h.httpcode.NOT_FOUND)
    h.Asserter.assert_content_type(res, h.CTS.html)


def test_utils_uuid(testapp):
    res = testapp.get(h.url_for("test.return_uuid"))
    h.Asserter.assert_false(uuid.check_uuid("fake uuid"))
    h.Asserter.assert_true(uuid.check_uuid(uuid.get_uuid(hexify=False)))
    h.Asserter.assert_true(uuid.check_uuid(res.json.get("uuid1"), ver=1))
    h.Asserter.assert_true(uuid.check_uuid(res.json.get("uuid3"), ver=3))
    h.Asserter.assert_true(uuid.check_uuid(res.json.get("uuid4")))
    h.Asserter.assert_true(uuid.check_uuid(res.json.get("uuid5"), ver=5))


def test_crypto(testapp):
    passwd = "my-favourite-password"
    crypto = ExtProxy("argon2")
    res = testapp.get(h.url_for("test.crypt", passwd=passwd))
    h.Asserter.assert_true(crypto.verify_hash(res.data, passwd))
    h.Asserter.assert_false(crypto.verify_hash(res.data, "wrong-pass"))


def test_utils_http_client_simple(testapp):
    with testapp.application.test_request_context():
        api = FlaskelHttp(HOSTS.apitester, token="pippo", dump_body=True)
        res = api.delete("/status/202")
        h.Asserter.assert_equals(res.status, h.httpcode.ACCEPTED)
        res = api.patch("/status/400")
        h.Asserter.assert_equals(res.status, h.httpcode.BAD_REQUEST)


def test_utils_http_client_exception(testapp):
    logger = testapp.application.logger
    api = HTTPClient(HOSTS.apitester, token="pippo", raise_on_exc=True, logger=logger)
    fake_api = HTTPClient(HOSTS.fake, username="test", password="test", logger=logger)

    res = fake_api.put("/", timeout=0.1)
    h.Asserter.assert_equals(res.status, h.httpcode.SERVICE_UNAVAILABLE)
    try:
        api.request("/status/500", h.HttpMethod.PUT)
    except HTTPStatusError as exc:
        h.Asserter.assert_equals(
            exc.response.status_code, h.httpcode.INTERNAL_SERVER_ERROR
        )
    try:
        fake_api.request("/", timeout=0.1)
    except werkzeug.exceptions.HTTPException as exc:
        h.Asserter.assert_equals(exc.code, h.httpcode.INTERNAL_SERVER_ERROR)


def test_utils_http_client_filename():
    filename = "pippo.txt"
    hdr = "Content-Disposition"
    param = {hdr: None}

    api = HTTPClient(HOSTS.apitester, dump_body=True)
    res = api.get("/not-found")
    h.Asserter.assert_status_code(res, h.httpcode.NOT_FOUND)

    param[hdr] = f"attachment; filename={filename}"
    res = api.get("/response-headers", params=param)
    h.Asserter.assert_equals(api.response_filename(res.headers), filename)

    param[hdr] = f"filename={filename}"
    res = api.post("/response-headers", params=param)
    h.Asserter.assert_equals(api.response_filename(res.headers), filename)

    param[hdr] = filename
    res = api.post("/response-headers", params=param)
    h.Asserter.assert_none(api.response_filename(res.headers))


def test_http_client_batch(testapp):
    with testapp.application.test_request_context():
        responses = batch.FlaskelHTTPBatch(
            logger=DummyLogger(), dump_body=(True, False)
        ).request(
            [
                dict(
                    url=f"{HOSTS.apitester}/anything",
                    method=h.HttpMethod.GET,
                    headers={"HDR1": "HDR1"},
                ),
                dict(
                    url=f"{HOSTS.apitester}/status/{h.httpcode.NOT_FOUND}",
                    method=h.HttpMethod.GET,
                ),
                dict(url=HOSTS.fake, method=h.HttpMethod.GET, timeout=0.1),
            ]
        )
    h.Asserter.assert_equals(responses[0].body.headers.Hdr1, "HDR1")
    h.Asserter.assert_equals(responses[1].status, h.httpcode.NOT_FOUND)
    h.Asserter.assert_equals(responses[2].status, h.httpcode.SERVICE_UNAVAILABLE)


def test_utils_http_jsonrpc_client(testapp):
    params = dict(a=1, b=2)
    with testapp.application.test_request_context():
        api = FlaskelJsonRPC(HOSTS.apitester, "/anything")
        res = api.request("method.test", params=params)
        h.Asserter.assert_equals(res.json.jsonrpc, "2.0")
        h.Asserter.assert_equals(res.json.id, api.request_id)
        h.Asserter.assert_equals(res.json.params, params)


def test_healthcheck(testapp):
    res = h.api_tester(
        testapp,
        url=testapp.application.config.HEALTHCHECK_PATH,
        status=h.httpcode.SERVICE_UNAVAILABLE,
        schema=schemas.SCHEMAS.HEALTHCHECK,
    )
    h.Asserter.assert_content_type(res, h.CTS.json_health)
    h.Asserter.assert_allin(
        res.json.checks.keys(), ("mongo", "redis", "sqlalchemy", "system", "services")
    )


def test_api_jsonrpc_success(app_dev):
    call_id = 1
    url = h.url_for("api.jsonrpc")
    client = TestJsonRPC(app_dev.test_client(), endpoint=url)
    client.perform(request=dict(method="MyJsonRPC.testAction1", id=call_id))
    h.Asserter.assert_equals(client.json.id, call_id)
    h.Asserter.assert_true(client.json.result.action1)

    res = app_dev.test_client().jsonrpc(url, method="MyJsonRPC.testAction2")
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)


def test_api_jsonrpc_error(app_dev):
    call_id = 1
    url = h.url_for("api.jsonrpc")
    testapp = app_dev.test_client()
    response_schema = schemas.SCHEMAS.JSONRPC.RESPONSE
    headers = dict(
        headers={app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    )

    res = testapp.jsonrpc(url, method="NotFoundMethod", call_id=call_id, **headers)
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCMethodNotFound().code)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.id, call_id)
    h.Asserter.assert_true(res.json.error.message)

    res = testapp.jsonrpc(url, json={}, **headers)
    h.Asserter.assert_status_code(res, h.httpcode.BAD_REQUEST)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCParseError().code)

    res = testapp.jsonrpc(url, json={"params": None}, **headers)
    h.Asserter.assert_status_code(res, h.httpcode.BAD_REQUEST)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = testapp.jsonrpc(
        url, json={"jsonrpc": 1, "method": "MyJsonRPC.testAction1"}, **headers
    )
    h.Asserter.assert_status_code(res, h.httpcode.BAD_REQUEST)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = testapp.jsonrpc(
        url, method="MyJsonRPC.testInternalError", call_id=call_id, **headers
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCInternalError().code)


def test_api_jsonrpc_params(app_dev):
    url = h.url_for("api.jsonrpc")
    method = "MyJsonRPC.testInvalidParams"
    testapp = app_dev.test_client()
    response_schema = schemas.SCHEMAS.JSONRPC.RESPONSE
    headers = dict(
        headers={app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    )

    res = testapp.jsonrpc(
        url, method=method, call_id=1, params={"param": "testparam"}, **headers
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_not_in("error", res.json)

    res = testapp.jsonrpc(
        url, method=method, call_id=1, params={"params": None}, **headers
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_schema(res.json, response_schema)
    h.Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidParams().code)


def test_api_jsonrpc_batch(app_dev):
    url = h.url_for("api.jsonrpc")
    testapp = app_dev.test_client()
    headers = dict(
        headers={app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    )
    res = testapp.jsonrpc_batch(
        url,
        requests=(
            dict(method="MyJsonRPC.testAction1", call_id=1, params={}),
            dict(method="MyJsonRPC.NotFoundMethod", call_id=2),
        ),
        **headers,
    )
    h.Asserter.assert_status_code(res, h.httpcode.MULTI_STATUS)
    h.Asserter.assert_true(res.json[0].result.action1)
    h.Asserter.assert_equals(res.json[1].error.code, rpc.RPCMethodNotFound().code)

    res = testapp.jsonrpc_batch(
        url,
        requests=(
            dict(method="MyJsonRPC.testAction1", call_id=1, params={}),
            dict(method="MyJsonRPC.NotFoundMethod", call_id=2),
            dict(method="MyJsonRPC.NotFoundMethod", call_id=3),
        ),
        **headers,
    )
    h.Asserter.assert_status_code(res, h.httpcode.REQUEST_ENTITY_TOO_LARGE)


def test_api_jsonrpc_notification(app_dev):
    url = h.url_for("api.jsonrpc")
    testapp = app_dev.test_client()
    headers = dict(
        headers={app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    )
    res = testapp.jsonrpc_batch(
        url,
        requests=(
            dict(method="MyJsonRPC.testAction1", params={}),
            dict(method="MyJsonRPC.NotFoundMethod"),
        ),
        **headers,
    )
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)

    res = testapp.jsonrpc_batch(
        url,
        requests=(
            dict(method="MyJsonRPC.testAction1", call_id=1, params={}),
            dict(method="MyJsonRPC.NotFoundMethod"),
        ),
        **headers,
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(len(res.json), 1)


def test_useragent(testapp):
    res = testapp.get(h.url_for("test.useragent"))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_allin(res.json.keys(), ("browser", "device", "os", "raw"))
    ua_string = """
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)
        Chrome/70.0.3538.77 Safari/537.36
    """
    res = useragent.UserAgent().parse(ua_string)
    h.Asserter.assert_equals(res.raw, ua_string)


def test_utils_date_conversion():
    exc = False
    fmt = "%d %B %Y %I:%M %p"
    iso_date = "2020-12-28T19:53:00"
    pretty_date = not_iso_date = "28 December 2020 07:53 PM"
    invalid_date = "invalid_date"
    DateHelper = datetime.DateHelper
    datetime_iso = DateHelper.str_to_date(iso_date, is_iso=True)

    res = datetime.from_iso_format(iso_date, fmt, exc=exc)
    h.Asserter.assert_true(res)
    h.Asserter.assert_equals(not_iso_date, res)

    res = datetime.to_iso_format(not_iso_date, fmt, exc=exc)
    h.Asserter.assert_true(res)
    h.Asserter.assert_equals(iso_date, res)
    res = datetime.to_iso_format(not_iso_date, exc=exc)
    h.Asserter.assert_true(res)
    h.Asserter.assert_equals(iso_date, res)

    h.Asserter.assert_none(datetime.from_iso_format(invalid_date, fmt, exc=exc))
    h.Asserter.assert_none(datetime.to_iso_format(invalid_date, fmt, exc=exc))

    h.Asserter.assert_true(DateHelper.is_weekend("5 September 2021"))
    h.Asserter.assert_false(DateHelper.is_weekend("2 September 2021"))

    h.Asserter.assert_equals(DateHelper.pretty_date(iso_date), pretty_date)
    h.Asserter.assert_equals(DateHelper.pretty_date(datetime_iso), pretty_date)


def test_correlation_id(testapp):
    cap = testapp.application
    request_id_header = cap.config.REQUEST_ID_HEADER

    res = testapp.get("/")
    h.Asserter.assert_header(res, request_id_header, is_in=True)
    h.Asserter.assert_type(res.headers[request_id_header], str)

    req_id = uuid.get_uuid()
    res = testapp.get("/", headers={request_id_header: req_id})
    h.Asserter.assert_header(res, request_id_header, req_id)

    req_id = "invalid_req_id"
    res = testapp.get("/", headers={request_id_header: req_id})
    h.Asserter.assert_different(res.headers[request_id_header], req_id)


def test_jwt(app_dev):
    testapp = app_dev.test_client()
    conf = testapp.application.config
    bypass = {conf.LIMITER.BYPASS_KEY: conf.LIMITER.BYPASS_VALUE}

    tokens = testapp.post(
        h.url_for("api.token_access", expires_access=1),
        json=dict(email=conf.BASIC_AUTH_USERNAME, password=conf.BASIC_AUTH_PASSWORD),
    )
    h.Asserter.assert_status_code(tokens)
    check = testapp.get(
        h.url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    h.Asserter.assert_status_code(check)
    time.sleep(2)
    check = testapp.get(
        h.url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    h.Asserter.assert_status_code(check, h.httpcode.UNAUTHORIZED)

    tokens = testapp.post(
        h.url_for("api.token_access"),
        json=dict(email=conf.BASIC_AUTH_USERNAME, password=conf.BASIC_AUTH_PASSWORD),
        headers=bypass,
    )
    h.Asserter.assert_status_code(tokens)
    h.Asserter.assert_allin(
        tokens.json.keys(),
        (
            "access_token",
            "refresh_token",
            "expires_in",
            "issued_at",
            "token_type",
            "scope",
        ),
    )

    res = testapp.post(
        h.url_for("api.token_refresh"),
        headers={"Authorization": f"Bearer {tokens.json.refresh_token}", **bypass},
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_allin(
        res.json.keys(),
        ("access_token", "expires_in", "issued_at", "token_type", "scope"),
    )

    check = testapp.get(
        h.url_for("api.token_check"),
        headers={"Authorization": f"Bearer {res.json.access_token}", **bypass},
    )
    h.Asserter.assert_status_code(check)

    unauth = testapp.get(
        h.url_for("api.token_check"),
        headers={"Authorization": "Bearer invalid-token", **bypass},
    )
    h.Asserter.assert_status_code(unauth, h.httpcode.UNAUTHORIZED)

    revoked = testapp.post(
        h.url_for("api.token_revoke"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
        json={
            "access_token": tokens.json.access_token,
            "refresh_token": tokens.json.refresh_token,
        },
    )
    h.Asserter.assert_status_code(revoked, h.httpcode.NO_CONTENT)

    res = testapp.get(
        h.url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    h.Asserter.assert_status_code(res, h.httpcode.UNAUTHORIZED)


def test_http_status():
    h.Asserter.assert_true(h.httpcode.is_informational(h.httpcode.PROCESSING))
    h.Asserter.assert_true(h.httpcode.is_success(h.httpcode.CREATED))
    h.Asserter.assert_false(h.httpcode.is_success(h.httpcode.MULTIPLE_CHOICES))
    h.Asserter.assert_true(h.httpcode.is_redirection(h.httpcode.SEE_OTHER))
    h.Asserter.assert_false(h.httpcode.is_redirection(h.httpcode.BAD_REQUEST))
    h.Asserter.assert_true(h.httpcode.is_client_error(h.httpcode.UNAUTHORIZED))
    h.Asserter.assert_false(
        h.httpcode.is_client_error(h.httpcode.INTERNAL_SERVER_ERROR)
    )
    h.Asserter.assert_true(h.httpcode.is_server_error(h.httpcode.NOT_IMPLEMENTED))
    h.Asserter.assert_false(h.httpcode.is_server_error(h.httpcode.NOT_MODIFIED))
    h.Asserter.assert_true(h.httpcode.is_ok(h.httpcode.FOUND))
    h.Asserter.assert_false(h.httpcode.is_ko(h.httpcode.SUCCESS))
    h.Asserter.assert_status_code(
        ObjectDict(status=201), code=(201, 202, 203), is_in=True
    )
    h.Asserter.assert_status_code(
        ObjectDict(status=201), code=(200, 299), in_range=True
    )
    h.Asserter.assert_status_code(ObjectDict(status=400), code=300, greater=True)
    h.Asserter.assert_status_code(ObjectDict(status=200), code=300, less=True)


def test_proxy_view(app_dev):
    testapp = app_dev.test_client()
    res = testapp.post(h.url_for("api.proxyview", p="v1"), json={"test": "test"})
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json.json.test, "test")
    h.Asserter.assert_equals(res.json.args.p, "v1")

    res = testapp.get(h.url_for("api.confproxy"))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json.headers.k, "v")
    h.Asserter.assert_equals(res.json.params.k, "v")


def test_jsonrpc_proxy_view(app_dev):
    testapp = app_dev.test_client()
    res = testapp.post(h.url_for("api.jsonrpc_proxyview"), json={"test": "test"})
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)

    res = testapp.get(h.url_for("api.jsonrpc_proxyview", param1=1, param2=2))
    h.Asserter.assert_status_code(res)
    response = json.loads(res.json.data)
    h.Asserter.assert_schema(response, schemas.SCHEMAS.JSONRPC.REQUEST)
    h.Asserter.assert_equals(response["method"], "jsonrpc_method")
    h.Asserter.assert_equals(response["params"]["param1"], "1")
    h.Asserter.assert_equals(response["params"]["param2"], "2")


def test_proxy_schema(app_dev):
    view = "api.schema_proxy"
    testapp = app_dev.test_client()
    bypass = {app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    _ = h.api_tester(
        testapp,
        h.url_for(view, filepath="pippo"),
        status=h.httpcode.NOT_FOUND,
        headers=bypass,
    )

    res = h.api_tester(testapp, h.url_for(view, filepath="jsonrpc/request.json"))
    h.Asserter.assert_equals(res.json, app_dev.config.SCHEMAS.JSONRPC.REQUEST)

    res = h.api_tester(testapp, h.url_for(view, filepath="api_problem"))
    h.Asserter.assert_equals(res.json, app_dev.config.SCHEMAS.API_PROBLEM)


def test_apidoc(testapp):
    res = testapp.get(h.url_for("api.apidocs"))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.html)

    res = testapp.get(h.url_for("api.apispec"))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.json)
    h.Asserter.assert_equals(res.json.info.version, "1.0.0")
    h.Asserter.assert_equals(res.json.servers[0].variables.context.default, "/")
    h.Asserter.assert_equals(
        res.json.servers[0].variables.host.default, "https://127.0.0.1:5000"
    )


def test_mobile_release(app_dev):
    agent = {"agent": "ios"}
    version = "1.0.0"
    testapp = app_dev.test_client()
    res = testapp.delete(h.url_for("api.mobile_release", **agent))
    h.Asserter.assert_status_code(res)
    res = testapp.delete(h.url_for("api.mobile_release", all="true", **agent))
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)

    res = testapp.post(h.url_for("api.mobile_release", ver=version, **agent))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json, 1)
    h.Asserter.assert_allin(res.json[0], ("critical", "version"))

    res = testapp.get(h.url_for("api.mobile_release", all="true", **agent))
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_allin(res.json[0], ("critical", "version"))

    res = testapp.post(h.url_for("api.mobile_release", ver=version, **agent))
    h.Asserter.assert_status_code(res, h.httpcode.BAD_REQUEST)

    bypass = {app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    res = testapp.get(
        h.url_for("api.mobile_release", ver="latest", **agent), headers=bypass
    )
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_header(res, "Content-Type", h.CTS.text)
    h.Asserter.assert_equals(res.data, version.encode())


def test_mobile_version(app_dev):
    testapp = app_dev.test_client()
    upgrade_header = app_dev.config.VERSION_UPGRADE_HEADER
    version_header = app_dev.config.VERSION_API_HEADER
    mobile_version = app_dev.config.VERSION_HEADER_KEY
    agent_header = app_dev.config.VERSION_AGENT_HEADER

    headers = {
        app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE,
        agent_header: "ios",
    }
    res = testapp.get(
        h.url_for("web.index"), headers={mobile_version: "0.0.0", **headers}
    )
    h.Asserter.assert_header(res, upgrade_header, "0")
    h.Asserter.assert_header(res, version_header, "1.0.0")

    url = h.url_for("api.mobile_release", ver="1.0.1", critical="true", agent="ios")
    res = testapp.post(url, headers=headers)
    h.Asserter.assert_status_code(res)
    res = testapp.get(
        h.url_for("web.index"), headers={mobile_version: "0.0.0", **headers}
    )
    h.Asserter.assert_header(res, upgrade_header, "1")

    res = testapp.get("/web-page-not-found")
    h.Asserter.assert_not_in(upgrade_header, list(res.headers.keys()))
    h.Asserter.assert_not_in(version_header, list(res.headers.keys()))


def test_mobile_views(app_dev):
    testapp = app_dev.test_client()
    url = h.url_for("api.mobile_logger")
    data = {"stacktrace": "exception"}

    res = testapp.post(url, json=data)
    h.Asserter.assert_status_code(res, h.httpcode.NO_CONTENT)

    res = testapp.post(f"{url}?debug", json=data)
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_equals(res.json, data)


def test_restful(app_dev):
    h.restful_tester(
        app_dev.test_client(),
        view="api.items",
        schema_read=schemas.SCHEMAS.ITEM,
        schema_collection=schemas.SCHEMAS.ITEM_LIST,
        body_create=dict(item="test"),
        headers={
            app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE,
            **h.basic_auth_header(),
        },
    )

    client = TestRestApi(app_dev.test_client(), endpoint=h.url_for("api.items"))
    client.test_post(
        request=dict(json=dict(item="test"), headers=h.basic_auth_header()),
        response=dict(schema=schemas.SCHEMAS.ITEM),
    )
    res_id = client.json.id
    client.test_get(
        res_id,
        request=dict(headers=h.basic_auth_header()),
        response=dict(schema=schemas.SCHEMAS.ITEM),
    )
    client.test_put(
        res_id,
        request=dict(json=dict(item="test"), headers=h.basic_auth_header()),
        response=dict(schema=schemas.SCHEMAS.ITEM),
    )
    client.test_collection(
        request=dict(headers=h.basic_auth_header()),
        response=dict(schema=schemas.SCHEMAS.ITEM_LIST),
    )
    client.test_delete(res_id, request=dict(headers=h.basic_auth_header()))


def test_misc():
    h.Asserter.assert_less(1, 2)
    h.Asserter.assert_greater(2, 1)
    h.Asserter.assert_range(2, (1, 3))
    h.Asserter.assert_occurrence("abacca", r"a", 3)
    h.Asserter.assert_occurrence("abacca", r"a", 4, less=True)
    h.Asserter.assert_occurrence("abacca", r"a", 2, greater=True)
    h.Asserter.assert_true(misc.to_float("1.1"))
    h.Asserter.assert_none(misc.to_float("1,1"))
    h.Asserter.assert_true(misc.to_int("1"))
    h.Asserter.assert_none(misc.to_int("1,1"))
    h.Asserter.assert_true(misc.parse_value("true"))
    h.Asserter.assert_equals("test", misc.parse_value("test"))
    h.Asserter.assert_equals(
        misc.to_int, misc.import_from_module("flaskel.utils.misc:to_int")
    )


def test_ipban(app_dev):  # must be last test
    res = None
    conf = app_dev.config
    ipban = ExtProxy("ipban")
    ipban.remove_whitelist("127.0.0.1")
    for _ in range(0, conf.IPBAN_COUNT * 2):
        testapp = app_dev.test_client()
        res = testapp.get("/phpmyadmin")

    h.Asserter.assert_status_code(res, h.httpcode.FORBIDDEN)
