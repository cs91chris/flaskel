from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.mixins import Asserter

from flaskel.ext.auth import TokenInfo
from flaskel.extra.apidoc import ApiSpecTemplate
from flaskel.tester.helpers import config, ApiTester, url_for
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from .views import (
    bp_api,
    bp_web,
    TokenAuthView,
    ApiDocTemplate,
    IndexTemplate,
    StaticFileView,
)


class TokenViews:
    check_token = "api.token_check"
    access_token = "api.token_access"
    refresh_token = "api.token_refresh"
    revoke_token = "api.token_revoke"


def test_apidoc(testapp):
    app = testapp(views=(ApiDocTemplate, ApiSpecTemplate))
    client = ApiTester(app.test_client())

    client.get(view=ApiDocTemplate.default_view_name, mimetype=ContentTypeEnum.HTML)

    res = client.get(
        view=ApiSpecTemplate.default_view_name, mimetype=ContentTypeEnum.JSON
    )
    Asserter.assert_different(res.json, {})


def test_jwt(testapp):
    app = testapp(
        config=ObjectDict(SCHEMAS=DEFAULT_SCHEMAS), views=((TokenAuthView, bp_api),)
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)
    token_header = client.token_header(access_view=TokenViews.access_token)

    tokens = client.post(
        view=TokenViews.access_token,
        json=dict(email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD),
        schema=config.SCHEMAS.ACCESS_TOKEN,
    )

    token_info = client.get(
        view=TokenViews.check_token,
        headers=token_header(token=tokens.json.access_token),
    )
    Asserter.assert_equals(token_info.json, TokenInfo(**token_info.json).to_dict())

    client.post(
        view=TokenViews.access_token,
        json=dict(email=config.ADMIN_EMAIL, password="bad password"),
        status=httpcode.UNAUTHORIZED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )

    client.post(
        view=TokenViews.refresh_token,
        headers=token_header(token=tokens.json.refresh_token),
        schema=config.SCHEMAS.REFRESH_TOKEN,
    )

    client.post(
        view=TokenViews.revoke_token,
        json=dict(
            access_token=tokens.json.access_token,
            refresh_token=tokens.json.refresh_token,
        ),
        status=httpcode.NO_CONTENT,
    )

    client.post(
        view=TokenViews.refresh_token,
        headers=token_header(token=tokens.json.refresh_token),
        status=httpcode.UNAUTHORIZED,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
        schema=config.SCHEMAS.API_PROBLEM,
    )


def test_template_view(testapp):
    app = testapp(views=(IndexTemplate,))
    client = ApiTester(app.test_client())
    response = client.get(
        view=IndexTemplate.default_view_name, mimetype=ContentTypeEnum.HTML
    )
    Asserter.assert_in("TITLE", response.get_data(as_text=True))
    Asserter.assert_in("USERNAME", response.get_data(as_text=True))


def test_static_file_view(testapp):
    app = testapp(views=((StaticFileView, bp_web),))
    client = ApiTester(app.test_client())
    response = client.get(
        url=url_for("web.assets", filename="css/style.css"),
        mimetype=ContentTypeEnum.CSS,
    )
    Asserter.assert_header(
        response, HeaderEnum.CONTENT_LENGTH, r"^[1-9][0-9]*$", regex=True
    )


def test_spa_view(testapp):
    # TODO: added missing tests
    assert True
