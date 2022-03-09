from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.mixins import Asserter

from flaskel.ext.auth import TokenInfo
from flaskel.extra.apidoc import ApiSpecTemplate
from flaskel.tester.helpers import config, ApiTester
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from flaskel.views import RenderTemplate
from .components import bp_api
from .views import TokenAuthView, VIEWS, ApiDocTemplate


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

    client.post(
        view=VIEWS.refresh_token,
        headers=token_header(token=tokens.json.refresh_token),
        status=httpcode.UNAUTHORIZED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )


def test_template_view(testapp):
    class IndexTemplate(RenderTemplate):
        def service(self, *_, **kwargs):
            return ObjectDict(username="USERNAME", title="TITLE")

    app = testapp(views=(IndexTemplate,))
    client = ApiTester(app.test_client())
    response = client.get(view=VIEWS.index, mimetype=ContentTypeEnum.HTML)
    Asserter.assert_in("TITLE", response.get_data(as_text=True))
    Asserter.assert_in("USERNAME", response.get_data(as_text=True))
