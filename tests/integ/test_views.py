from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.jsonschema.support import Fields
from vbcore.tester.mixins import Asserter

from flaskel.ext.auth import TokenInfo
from flaskel.extra.apidoc import ApiSpecTemplate
from flaskel.tester.helpers import config, ApiTester, url_for
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from flaskel.views import RenderTemplate
from flaskel.views.proxy import TransparentProxyView, SchemaProxyView, JsonRPCProxy
from .components import bp_api
from .helpers import HOSTS
from .views import TokenAuthView, VIEWS, ApiDocTemplate, APIResource


def test_apidoc(testapp):
    app = testapp(views=(ApiDocTemplate, ApiSpecTemplate))
    client = ApiTester(app.test_client())

    client.get(view=VIEWS.api_docs, mimetype=ContentTypeEnum.HTML)

    res = client.get(view=VIEWS.api_specs, mimetype=ContentTypeEnum.JSON)
    Asserter.assert_different(res.json, {})


def test_jwt(testapp):
    app = testapp(
        config=ObjectDict(SCHEMAS=DEFAULT_SCHEMAS), views=((TokenAuthView, bp_api),)
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)
    token_header = client.token_header(access_view=VIEWS.access_token)

    tokens = client.post(
        view=VIEWS.access_token,
        json=dict(email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD),
        schema=config.SCHEMAS.ACCESS_TOKEN,
    )

    token_info = client.get(
        view=VIEWS.check_token,
        headers=token_header(token=tokens.json.access_token),
    )
    Asserter.assert_equals(token_info.json, TokenInfo(**token_info.json).to_dict())

    client.post(
        view=VIEWS.access_token,
        json=dict(email=config.ADMIN_EMAIL, password="bad password"),
        status=httpcode.UNAUTHORIZED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )

    client.post(
        view=VIEWS.refresh_token,
        headers=token_header(token=tokens.json.refresh_token),
        schema=config.SCHEMAS.REFRESH_TOKEN,
    )

    client.post(
        view=VIEWS.revoke_token,
        json=dict(
            access_token=tokens.json.access_token,
            refresh_token=tokens.json.refresh_token,
        ),
        status=httpcode.NO_CONTENT,
    )

    # TODO uncomment when using redis client instead of a mock
    # client.post(
    #     VIEWS.refresh_token,
    #     headers=token_header(token=tokens.json.refresh_token),
    #     status=httpcode.UNAUTHORIZED
    # )


def test_template_view(testapp):
    class IndexTemplate(RenderTemplate):
        def service(self, *_, **kwargs):
            return ObjectDict(username="USERNAME", title="TITLE")

    app = testapp(views=(IndexTemplate,))
    client = ApiTester(app.test_client())
    response = client.get(view=VIEWS.index, mimetype=ContentTypeEnum.HTML)
    Asserter.assert_in("TITLE", response.get_data(as_text=True))
    Asserter.assert_in("USERNAME", response.get_data(as_text=True))


def test_api_resource(testapp):
    conf = ObjectDict(
        SCHEMAS=ObjectDict(
            ITEM_POST=Fields.object(
                properties={"item": Fields.string},
            ),
            ITEM=Fields.object(
                properties={"id": Fields.integer, "item": Fields.string}
            ),
            ITEM_LIST=Fields.array_object(
                properties={"id": Fields.integer, "item": Fields.string}
            ),
        )
    )
    app = testapp(config=conf, views=(APIResource,))
    client = ApiTester(app.test_client())

    client.restful(
        view="resources",
        schema_read=config.SCHEMAS.ITEM,
        schema_collection=config.SCHEMAS.ITEM_LIST,
        body_create={"item": "TEST"},
        body_update={"id": 1, "item": "TEST"},
    )


def test_proxy_view(testapp):
    app = testapp(
        views=((TransparentProxyView, dict(host=HOSTS.apitester, url="/anything")),)
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)
    response = client.get(
        view=VIEWS.index,
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
        url=url_for(VIEWS.schema_proxy, filepath="api_problem"),
        mimetype=ContentTypeEnum.JSON,
    )
    Asserter.assert_equals(response.json, DEFAULT_SCHEMAS.API_PROBLEM)

    client.get(
        url=url_for(VIEWS.schema_proxy, filepath="not_found"),
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
                        {
                            "url": "/search/<path:action>",
                            "endpoint": "proxy_searches",
                        },
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
