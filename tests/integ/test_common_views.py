from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.mixins import Asserter

from flaskel.ext.auth import TokenInfo
from flaskel.extra.apidoc import ApiSpecTemplate
from flaskel.tester.helpers import ApiTester, config, url_for
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS

from .views import ApiDocTemplate, bp_api, IndexTemplate, StaticFileView, TokenAuthView


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
    Asserter.assert_schema(res.json, DEFAULT_SCHEMAS.OPENAPI)


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
    app = testapp(
        config=ObjectDict(USE_X_SENDFILE=False),
        views=((StaticFileView, bp_api),),
    )
    client = ApiTester(app.test_client())

    response = client.get(
        url=url_for("api.assets", filename="css/style.css"),
        mimetype=ContentTypeEnum.CSS,
        status=httpcode.SUCCESS,
    )
    Asserter.assert_equals(
        len(response.get_data(as_text=True)),
        int(response.headers[HeaderEnum.CONTENT_LENGTH]),
    )


def test_use_x_send_file(testapp):
    app = testapp(
        config=ObjectDict(USE_X_SENDFILE=True, ENABLE_ACCEL=True),
        views=((StaticFileView, bp_api, {"name": "protected_assets"}),),
    )
    client = ApiTester(app.test_client())

    response = client.get(
        url=url_for("api.protected_assets", filename="css/style.css"),
        mimetype=ContentTypeEnum.CSS,
        status=httpcode.SUCCESS,
    )

    Asserter.assert_equals(len(response.get_data(as_text=True)), 0)
    Asserter.assert_greater(int(response.headers[HeaderEnum.CONTENT_LENGTH]), 0)
    Asserter.assert_true(
        response.headers[HeaderEnum.X_ACCEL_REDIRECT].endswith(
            f"{StaticFileView.default_static_path}/css/style.css"
        )
    )
    Asserter.assert_headers(
        response,
        {
            HeaderEnum.X_ACCEL_BUFFERING: "yes",
            HeaderEnum.X_ACCEL_CHARSET: app.config.ACCEL_CHARSET,
            HeaderEnum.X_ACCEL_LIMIT_RATE: app.config.ACCEL_LIMIT_RATE,
            HeaderEnum.X_ACCEL_EXPIRES: app.config.SEND_FILE_MAX_AGE_DEFAULT,
            HeaderEnum.CONTENT_DISPOSITION: "attachment; filename=style.css",
        },
    )


def test_spa_view(testapp):
    # TODO: added missing tests
    _ = testapp
    assert True
