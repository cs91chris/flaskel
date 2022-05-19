from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.helpers import basic_auth_header
from vbcore.tester.mixins import Asserter

from flaskel.tester.helpers import url_for


def test_app_runs(api_tester):
    api_tester.get(
        url="/",
        status=httpcode.NOT_FOUND,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )


def test_cors_headers(api_tester, config):
    res = api_tester.get(
        url="/", status=httpcode.NOT_FOUND, mimetype=ContentTypeEnum.JSON_PROBLEM
    )
    Asserter.assert_header(res, HeaderEnum.ACCESS_CONTROL_ALLOW_ORIGIN, "*")
    Asserter.assert_allin(
        res.headers[HeaderEnum.ACCESS_CONTROL_EXPOSE_HEADERS].split(", "),
        config.CORS_EXPOSE_HEADERS,
    )


def test_apidoc(config, api_tester, views):
    headers = basic_auth_header(config.ADMIN_EMAIL, config.ADMIN_PASSWORD)

    api_tester.get(
        url=url_for(views.api_docs), headers=headers, mimetype=ContentTypeEnum.HTML
    )
    res = api_tester.get(
        url=url_for(views.api_spec), headers=headers, mimetype=ContentTypeEnum.JSON
    )
    Asserter.assert_different(res.json, {})


def test_jwt(api_tester, config, auth_token, views):
    tokens = api_tester.post(
        url_for(views.access_token),
        json=dict(email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD),
        schema=config.SCHEMAS.AccessToken,
    )
    token_refresh = auth_token(tokens.json.refresh_token)

    api_tester.post(
        url=url_for(views.access_token),
        json=dict(email=config.ADMIN_EMAIL, password="bad password"),
        status=httpcode.UNAUTHORIZED,
    )

    api_tester.post(
        url=url_for(views.refresh_token),
        headers=token_refresh,
        schema=config.SCHEMAS.RefreshToken,
    )

    api_tester.post(
        url=url_for(views.revoke_token),
        json=dict(
            access_token=tokens.json.access_token,
            refresh_token=tokens.json.refresh_token,
        ),
        status=httpcode.NO_CONTENT,
    )

    api_tester.post(
        url=url_for(views.refresh_token),
        headers=token_refresh,
        status=httpcode.UNAUTHORIZED,
    )
