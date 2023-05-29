from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.asserter import Asserter

from flaskel.ext.errors.dispatchers import URLPrefixDispatcher
from flaskel.tester.helpers import ApiTester, config


def test_app_runs(client):
    ApiTester(client).get(
        url="/",
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )


def test_method_not_allowed(client):
    res = ApiTester(client).post(
        url="/api",
        status=httpcode.METHOD_NOT_ALLOWED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )
    allowed = {"OPTIONS", "GET", "HEAD"}
    Asserter.assert_equals(set(res.headers["Allow"].split(", ")), allowed)
    Asserter.assert_equals(set(res.get_json()["response"]["allowed"]), allowed)


def test_api(client):
    res = ApiTester(client).get(
        url="/api",
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )
    Asserter.assert_equals(res.json["detail"], "error from app")


def test_api_error(client):
    res = ApiTester(client).get(
        url="/api/error",
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )
    Asserter.assert_equals(res.json["detail"], "Unhandled Exception")


def test_web(client):
    ApiTester(client).get(
        url="/web/web",
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.HTML,
    )


def test_web_redirect(client):
    res = ApiTester(client).get(
        url="/web/redirect",
        status=httpcode.PERMANENT_REDIRECT,
        mimetype=ContentTypeEnum.HTML,
    )
    Asserter.assert_equals(res.headers["Location"], "/web")


def test_web_xhr(client):
    ApiTester(client).get(
        url="/web/web",
        headers={"X-Requested-With": "XMLHttpRequest"},
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )


def test_web_error(client):
    ApiTester(client).get(
        url="/web/web",
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.HTML,
    )


def test_custom(client, app):
    ApiTester(client).get(
        url="/custom/custom",
        base_url="http://api." + app.config["SERVER_NAME"],
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.HTML,
    )


def test_dispatch_error_web(client, app, error_handler):
    error_handler.register_dispatcher(app, URLPrefixDispatcher)
    ApiTester(client).get(
        url="/web/web/page-not-found",
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.HTML,
    )


def test_dispatch_error_api(client, app):
    res = ApiTester(client).get(
        url="/api-not-found",
        base_url="http://api." + app.config["SERVER_NAME"],
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.HTML,
    )
    Asserter.assert_in("test", res.headers["custom"])


def test_dispatch_default(client, app, error_handler):
    error_handler.register_dispatcher(app, dispatcher="default")
    ApiTester(client).get(
        url="/not-found",
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.HTML,
    )
    ApiTester(client).post(
        url="/not-allowed",
        status=httpcode.METHOD_NOT_ALLOWED,
        mimetype=ContentTypeEnum.HTML,
    )


def test_permanent_redirect(client):
    res = ApiTester(client).get(
        url="/permanent",
        status=httpcode.PERMANENT_REDIRECT,
        mimetype=ContentTypeEnum.HTML,
    )
    Asserter.assert_equals(res.headers["Location"], "http://flask.dev:5000/permanent/")


def test_response(client):
    res = ApiTester(client).get(
        url="/api/response",
        status=httpcode.INTERNAL_SERVER_ERROR,
        mimetype=ContentTypeEnum.HTML,
    )
    Asserter.assert_equals(res.data, b"response")


def test_unauthorized(client):
    res = ApiTester(client).get(
        url="/api/unauthorized",
        status=httpcode.UNAUTHORIZED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )
    auth = res.get_json()["response"]["authenticate"][0]
    Asserter.assert_equals(res.headers["WWW-Authenticate"], "Basic realm=realm-name")
    Asserter.assert_equals(auth["auth_type"], "basic")
    Asserter.assert_equals(auth["realm"], "realm-name")


def test_retry_after(client):
    res = ApiTester(client).get(
        url="/api/retry",
        status=httpcode.TOO_MANY_REQUESTS,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )

    date = "Wed, 01 Mar 2000 00:00:00 GMT"
    response = res.get_json()["response"]
    Asserter.assert_equals(res.headers["Retry-After"], date)
    Asserter.assert_equals(response["retry_after"], date)


def test_range(client):
    res = ApiTester(client).get(
        url="/api/range",
        status=httpcode.RANGE_NOT_SATISFIABLE,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )

    Asserter.assert_equals(res.headers["Content-Range"], "bytes */10")

    data = res.get_json()["response"]
    Asserter.assert_equals(data["length"], 10)
    Asserter.assert_equals(data["units"], "bytes")
