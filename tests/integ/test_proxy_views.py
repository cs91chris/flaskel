from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.mixins import Asserter

from flaskel.tester.helpers import url_for, ApiTester
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from flaskel.views import UrlRule
from flaskel.views.proxy import JsonRPCProxy, SchemaProxyView, TransparentProxyView
from tests.integ.test_http_client import HOSTS
from tests.integ.views import bp_api


def test_proxy_view(testapp):
    app = testapp(
        views=((TransparentProxyView, dict(host=HOSTS.apitester, url="/anything")),)
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)
    response = client.get(
        view=TransparentProxyView.default_view_name,
        json={"a": "a"},
        headers={"X-Test": "test"},
        params={"test": "test"},
    )

    Asserter.assert_equals(response.json.method, "GET")
    Asserter.assert_equals(response.json.json, {"a": "a"})
    Asserter.assert_equals(response.json.args.test, "test")
    Asserter.assert_equals(response.json.headers["X-Test"], "test")


def test_schema_conf_proxy_view(testapp):
    app = testapp(
        config=ObjectDict(SCHEMAS=DEFAULT_SCHEMAS),
        views=((SchemaProxyView, bp_api),),
    )
    client = ApiTester(app.test_client())

    response = client.get(
        url=url_for("api.schema_proxy", filepath="api_problem"),
        mimetype=ContentTypeEnum.JSON,
    )
    Asserter.assert_equals(response.json, DEFAULT_SCHEMAS.API_PROBLEM)

    client.get(
        url=url_for("api.schema_proxy", filepath="not_found"),
        status=httpcode.NOT_FOUND,
        schema=DEFAULT_SCHEMAS.API_PROBLEM,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )


def test_jsonrpc_proxy_view(testapp):
    namespace = "Search"
    rpc_method = "test_method"
    params = dict(param1="1", param2="2")

    app = testapp(
        views=(
            (
                JsonRPCProxy,
                dict(
                    url=f"{HOSTS.apitester}/anything",
                    skip_args=("action",),
                    namespace=namespace,
                    urls=(
                        UrlRule(
                            url="/search/<path:action>",
                            endpoint="proxy_searches",
                        ),
                    ),
                ),
            ),
        )
    )
    url = url_for("proxy_searches", action=rpc_method)
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)

    response = client.get(url=url, params=params)
    Asserter.assert_schema(response.json.json, DEFAULT_SCHEMAS.JSONRPC.RESPONSE)
    Asserter.assert_equals(response.json.json.params, params)
    Asserter.assert_equals(response.json.json.method, f"{namespace}.{rpc_method}")

    client.post(url=url, json=params, status=httpcode.NO_CONTENT)
