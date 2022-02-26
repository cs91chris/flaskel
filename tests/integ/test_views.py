from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.jsonschema.support import Fields
from vbcore.tester.mixins import Asserter

from flaskel.extra.apidoc import ApiSpecTemplate
from flaskel.tester.helpers import get_access_token, config, ApiTester
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from .views import TokenAuthView, VIEWS, ApiDocTemplate, APIResource


def test_apidoc(testapp):
    app = testapp(views=(ApiDocTemplate, ApiSpecTemplate))
    client = ApiTester(app.test_client())

    client.get(view=VIEWS.api_docs, mimetype=ContentTypeEnum.HTML)

    res = client.get(view=VIEWS.api_specs, mimetype=ContentTypeEnum.JSON)
    Asserter.assert_different(res.json, {})


def test_jwt(testapp):
    app = testapp(config=ObjectDict(SCHEMAS=DEFAULT_SCHEMAS), views=(TokenAuthView,))
    client = ApiTester(app.test_client())

    tokens = client.post(
        view=VIEWS.access_token,
        json=dict(email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD),
        schema=config.SCHEMAS.ACCESS_TOKEN,
    )

    token_refresh = get_access_token(
        client, access_view=VIEWS.access_token, token=tokens.json.refresh_token
    )

    client.post(
        view=VIEWS.access_token,
        json=dict(email=config.ADMIN_EMAIL, password="bad password"),
        status=httpcode.UNAUTHORIZED,
    )

    client.post(
        view=VIEWS.refresh_token,
        headers=token_refresh,
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
    #     headers=token_refresh,
    #     status=httpcode.UNAUTHORIZED
    # )


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
