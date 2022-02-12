import json
import os
import time

from vbcore import uuid
from vbcore.http import httpcode, HttpMethod
from vbcore.tester.helpers import basic_auth_header
from vbcore.tester.http import TestHttpCall, TestHttpApi, TestRestApi
from vbcore.tester.mixins import Asserter

from flaskel.tester.helpers import url_for, CTS, api_tester, restful_tester
from flaskel.utils.datastruct import ExtProxy, ConfigProxy
from flaskel.utils.schemas.default import SCHEMAS


def test_app_dev(app_dev):
    Asserter.assert_equals(app_dev.config.FLASK_ENV, "development")
    Asserter.assert_equals(app_dev.config.SECRET_KEY, "fake_very_complex_string")

    client = TestHttpCall(app_dev.test_client())
    client.perform(request={"url": url_for("web.index")})

    client = TestHttpApi(app_dev.test_client())
    client.perform(request={"url": url_for("test.test_https")})
    Asserter.assert_equals(client.json.scheme, "https")
    Asserter.assert_true(client.json.url_for.startswith("https"))


def test_api_resources(testapp):
    res = testapp.get(url_for("api.resource_api"), headers={"Accept": CTS.xml})
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.xml)

    res = testapp.get(url_for("api.resource_api", res_id=1))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.json)

    res = testapp.get(url_for("api.resource_api", res_id=1, sub_resource="items"))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.json)

    res = testapp.get(url_for("api.resource_api", res_id=1, sub_resource="not-found"))
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.json_problem)
    Asserter.assert_schema(res.json, SCHEMAS.API_PROBLEM)
    Asserter.assert_equals(res.json.detail, "not found")

    res = testapp.get(url_for("api.resource_api", res_id=1, sub_resource="not-found"))
    Asserter.assert_status_code(res, httpcode.TOO_MANY_REQUESTS)

    time.sleep(int(res.headers.get("Retry-After") or 0))  # check rate limit
    res = testapp.delete(url_for("api.resource_api", res_id=1))
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    data = dict(item="test")
    res = testapp.put(url_for("api.resource_api", res_id=1), json=data)
    Asserter.assert_status_code(res)

    res = testapp.post(url_for("api.resource_api"), json=data)
    Asserter.assert_status_code(res, httpcode.CREATED)

    res = testapp.post(
        url_for("api.resource_api", res_id=1, sub_resource="items"), json=data
    )
    Asserter.assert_status_code(res, httpcode.CREATED)

    res = testapp.post(url_for("api.resource_api"), json={})
    Asserter.assert_status_code(res, httpcode.UNPROCESSABLE_ENTITY)
    Asserter.assert_allin(res.json.response.reason, ("cause", "message", "path"))


def test_api_cors(testapp):
    client = TestHttpApi(testapp)
    client.perform(
        request={"url": url_for("api.resource_api")},
        response={
            "status": {"code": httpcode.TOO_MANY_REQUESTS},
            "headers": {
                "Access-Control-Allow-Origin": {"value": "*"},
                "Content-Type": {"value": CTS.json_problem},
            },
        },
    )

    headers = testapp.application.config.CORS_EXPOSE_HEADERS
    res = api_tester(testapp, url="/")
    Asserter.assert_header(res, "Access-Control-Allow-Origin", "*")
    Asserter.assert_allin(
        res.headers["Access-Control-Expose-Headers"].split(", "), headers
    )


def test_dispatch_error_web(testapp):
    client = TestHttpCall(testapp)
    client.perform(
        request={"url": "/web-page-not-found"},
        response={"status": {"code": httpcode.NOT_FOUND}},
    )


def test_dispatch_error_api(testapp):
    client = TestHttpApi(testapp)
    client.perform(
        request={
            "url": f"http://api.{testapp.application.config.SERVER_NAME}/not_found"
        },
        response={
            "status": {"code": httpcode.NOT_FOUND},
            "headers": {"Content-Type": {"value": CTS.json_problem}},
            "schema": SCHEMAS.API_PROBLEM,
        },
    )


def test_force_https(testapp):
    _ = testapp.get(url_for("test.test_https"))
    client = TestHttpApi(testapp)
    client.perform(request={"url": url_for("test.test_https")})
    Asserter.assert_equals(client.json.scheme, "https")
    Asserter.assert_true(client.json.url_for.startswith("https"))


def test_reverse_proxy(testapp):
    res = testapp.get(
        url_for("test.test_proxy"), headers={"X-Forwarded-Prefix": "/test"}
    )
    Asserter.assert_status_code(res)
    Asserter.assert_true(bool(res.json.request_id))
    Asserter.assert_equals(res.json.script_name, "/test")
    Asserter.assert_equals(res.json.original.SCRIPT_NAME, "")


def test_secret_key_prod(testapp):
    Asserter.assert_equals(testapp.application.config.FLASK_ENV, "production")
    Asserter.assert_true(os.path.isfile(".secret.key"))
    os.remove(".secret.key")


def test_method_override(testapp):
    res = testapp.post(
        url_for("test.method_override_post"),
        headers={"X-HTTP-Method-Override": HttpMethod.PUT},
    )
    Asserter.assert_status_code(res)

    res = testapp.post(url_for("test.method_override_post", _method_override="PUT"))
    Asserter.assert_status_code(res)


def test_converters(testapp):
    res = testapp.get(url_for("test.list_converter", data=["a", "b", "c"]))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(len(res.json), 3)


def test_utils_get_json(testapp):
    res = testapp.post(url_for("test.get_invalid_json"))
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)


def test_utils_send_file(testapp):
    filename = "MANIFEST.in"
    url = url_for("test.download") + "?filename={}"

    res = testapp.get(url.format(filename))
    Asserter.assert_status_code(res)
    Asserter.assert_header(
        res, "Content-Disposition", f"attachment; filename={filename}"
    )
    Asserter.assert_header(res, "X-Accel-Redirect", f"./{filename}")
    Asserter.assert_true(res.headers.get("X-Sendfile").endswith(filename))
    Asserter.assert_equals(res.data, b"")

    res = testapp.get(url.format("nofile.txt"))
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.html)


def test_healthcheck(testapp):
    res = api_tester(
        testapp,
        url=testapp.application.config.HEALTHCHECK_PATH,
        status=httpcode.SERVICE_UNAVAILABLE,
        schema=SCHEMAS.HEALTHCHECK,
    )
    Asserter.assert_content_type(res, CTS.json_health)
    Asserter.assert_allin(
        res.json.checks.keys(), ("mongo", "redis", "sqlalchemy", "system", "services")
    )


def test_correlation_id(testapp):
    cap = testapp.application
    request_id_header = cap.config.REQUEST_ID_HEADER

    res = testapp.get("/")
    Asserter.assert_header(res, request_id_header, is_in=True)
    Asserter.assert_type(res.headers[request_id_header], str)

    req_id = uuid.get_uuid()
    res = testapp.get("/", headers={request_id_header: req_id})
    Asserter.assert_header(res, request_id_header, req_id)

    req_id = "invalid_req_id"
    res = testapp.get("/", headers={request_id_header: req_id})
    Asserter.assert_different(res.headers[request_id_header], req_id)


def test_jwt(app_dev):
    testapp = app_dev.test_client()
    conf = testapp.application.config
    bypass = {conf.LIMITER.BYPASS_KEY: conf.LIMITER.BYPASS_VALUE}

    tokens = testapp.post(
        url_for("api.token_access", expires_access=1),
        json=dict(email=conf.BASIC_AUTH_USERNAME, password=conf.BASIC_AUTH_PASSWORD),
    )
    Asserter.assert_status_code(tokens)
    check = testapp.get(
        url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    Asserter.assert_status_code(check)
    time.sleep(2)
    check = testapp.get(
        url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    Asserter.assert_status_code(check, httpcode.UNAUTHORIZED)

    tokens = testapp.post(
        url_for("api.token_access"),
        json=dict(email=conf.BASIC_AUTH_USERNAME, password=conf.BASIC_AUTH_PASSWORD),
        headers=bypass,
    )
    Asserter.assert_status_code(tokens)
    Asserter.assert_allin(
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
        url_for("api.token_refresh"),
        headers={"Authorization": f"Bearer {tokens.json.refresh_token}", **bypass},
    )
    Asserter.assert_status_code(res)
    Asserter.assert_allin(
        res.json.keys(),
        ("access_token", "expires_in", "issued_at", "token_type", "scope"),
    )

    check = testapp.get(
        url_for("api.token_check"),
        headers={"Authorization": f"Bearer {res.json.access_token}", **bypass},
    )
    Asserter.assert_status_code(check)

    unauth = testapp.get(
        url_for("api.token_check"),
        headers={"Authorization": "Bearer invalid-token", **bypass},
    )
    Asserter.assert_status_code(unauth, httpcode.UNAUTHORIZED)

    revoked = testapp.post(
        url_for("api.token_revoke"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
        json={
            "access_token": tokens.json.access_token,
            "refresh_token": tokens.json.refresh_token,
        },
    )
    Asserter.assert_status_code(revoked, httpcode.NO_CONTENT)

    res = testapp.get(
        url_for("api.token_check"),
        headers={"Authorization": f"Bearer {tokens.json.access_token}", **bypass},
    )
    Asserter.assert_status_code(res, httpcode.UNAUTHORIZED)


def test_proxy_view(app_dev):
    testapp = app_dev.test_client()
    res = testapp.post(url_for("api.proxyview", p="v1"), json={"test": "test"})
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.json.test, "test")
    Asserter.assert_equals(res.json.args.p, "v1")

    res = testapp.get(url_for("api.confproxy"))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.headers.k, "v")
    Asserter.assert_equals(res.json.params.k, "v")


def test_jsonrpc_proxy_view(app_dev):
    testapp = app_dev.test_client()
    res = testapp.post(url_for("api.jsonrpc_proxyview"), json={"test": "test"})
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    res = testapp.get(url_for("api.jsonrpc_proxyview", param1=1, param2=2))
    Asserter.assert_status_code(res)
    response = json.loads(res.json.data)
    Asserter.assert_schema(response, SCHEMAS.JSONRPC.REQUEST)
    Asserter.assert_equals(response["method"], "jsonrpc_method")
    Asserter.assert_equals(response["params"]["param1"], "1")
    Asserter.assert_equals(response["params"]["param2"], "2")


def test_proxy_schema(app_dev):
    view = "api.schema_proxy"
    testapp = app_dev.test_client()
    bypass = {app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    _ = api_tester(
        testapp,
        url_for(view, filepath="pippo"),
        status=httpcode.NOT_FOUND,
        headers=bypass,
    )

    res = api_tester(testapp, url_for(view, filepath="jsonrpc/request.json"))
    Asserter.assert_equals(res.json, app_dev.config.SCHEMAS.JSONRPC.REQUEST)

    res = api_tester(testapp, url_for(view, filepath="api_problem"))
    Asserter.assert_equals(res.json, app_dev.config.SCHEMAS.API_PROBLEM)


def test_apidoc(testapp):
    res = testapp.get(url_for("api.apidocs"))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.html)

    res = testapp.get(url_for("api.apispec"))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.json)
    Asserter.assert_equals(res.json.info.version, "1.0.0")
    Asserter.assert_equals(res.json.servers[0].variables.context.default, "/")
    Asserter.assert_equals(
        res.json.servers[0].variables.host.default, "https://127.0.0.1:5000"
    )


def test_mobile_release(app_dev):
    agent = {"agent": "ios"}
    version = "1.0.0"
    testapp = app_dev.test_client()
    res = testapp.delete(url_for("api.mobile_release", **agent))
    Asserter.assert_status_code(res)
    res = testapp.delete(url_for("api.mobile_release", all="true", **agent))
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    res = testapp.post(url_for("api.mobile_release", ver=version, **agent))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(len(res.json), 1)
    Asserter.assert_allin(res.json[0], ("critical", "version"))

    res = testapp.get(url_for("api.mobile_release", all="true", **agent))
    Asserter.assert_status_code(res)
    Asserter.assert_allin(res.json[0], ("critical", "version"))

    res = testapp.post(url_for("api.mobile_release", ver=version, **agent))
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)

    bypass = {app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE}
    res = testapp.get(
        url_for("api.mobile_release", ver="latest", **agent), headers=bypass
    )
    Asserter.assert_status_code(res)
    Asserter.assert_header(res, "Content-Type", CTS.text)
    Asserter.assert_equals(res.data, version.encode())


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
        url_for("web.index"), headers={mobile_version: "0.0.0", **headers}
    )
    Asserter.assert_header(res, upgrade_header, "0")
    Asserter.assert_header(res, version_header, "1.0.0")

    url = url_for("api.mobile_release", ver="1.0.1", critical="true", agent="ios")
    res = testapp.post(url, headers=headers)
    Asserter.assert_status_code(res)
    res = testapp.get(
        url_for("web.index"), headers={mobile_version: "0.0.0", **headers}
    )
    Asserter.assert_header(res, upgrade_header, "1")

    res = testapp.get("/web-page-not-found")
    Asserter.assert_not_in(upgrade_header, list(res.headers.keys()))
    Asserter.assert_not_in(version_header, list(res.headers.keys()))


def test_mobile_views(app_dev):
    testapp = app_dev.test_client()
    url = url_for("api.mobile_logger")
    data = {"stacktrace": "exception"}

    res = testapp.post(url, json=data)
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    res = testapp.post(f"{url}?debug", json=data)
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json, data)


def test_restful(app_dev):
    restful_tester(
        app_dev.test_client(),
        view="api.items",
        schema_read=ConfigProxy("SCHEMAS.ITEM"),
        schema_collection=ConfigProxy("SCHEMAS.ITEM_LIST"),
        body_create=dict(item="test"),
        headers={
            app_dev.config.LIMITER.BYPASS_KEY: app_dev.config.LIMITER.BYPASS_VALUE,
            **basic_auth_header(),
        },
    )

    client = TestRestApi(app_dev.test_client(), endpoint=url_for("api.items"))
    client.test_post(
        request=dict(json=dict(item="test"), headers=basic_auth_header()),
        response=dict(schema=ConfigProxy("SCHEMAS.ITEM")),
    )
    res_id = client.json.id
    client.test_get(
        res_id,
        request=dict(headers=basic_auth_header()),
        response=dict(schema=ConfigProxy("SCHEMAS.ITEM")),
    )
    client.test_put(
        res_id,
        request=dict(json=dict(item="test"), headers=basic_auth_header()),
        response=dict(schema=ConfigProxy("SCHEMAS.ITEM")),
    )
    client.test_collection(
        request=dict(headers=basic_auth_header()),
        response=dict(schema=ConfigProxy("SCHEMAS.ITEM_LIST")),
    )
    client.test_delete(res_id, request=dict(headers=basic_auth_header()))


def test_ipban(app_dev):  # must be last test
    res = None
    conf = app_dev.config
    ipban = ExtProxy("ipban")
    ipban.remove_whitelist("127.0.0.1")
    for _ in range(0, conf.IPBAN_COUNT * 2):
        testapp = app_dev.test_client()
        res = testapp.get("/phpmyadmin")

    Asserter.assert_status_code(res, httpcode.FORBIDDEN)
