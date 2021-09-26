import flask
import flask_jwt_extended

from flaskel.ext import builder
from flaskel.ext.auth import BaseTokenHandler
from flaskel import httpcode, cap, HttpMethod
from flaskel.utils import webargs
from flaskel.views import BaseView


class BaseTokenAuth(BaseView):
    jwt = flask_jwt_extended
    handler: BaseTokenHandler = None

    default_view_name = "token_auth"
    methods = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    """
        endpoint should not be change otherwise dispatch_request must change
    """
    default_urls = (
        {"url": "/token/access", "endpoint": "token_access"},
        {"url": "/token/refresh", "endpoint": "token_refresh"},
        {"url": "/token/revoke", "endpoint": "token_revoke"},
        {"url": "/token/check", "endpoint": "token_check"},
    )

    @classmethod
    def check_credential(cls):
        data = flask.request.json
        if (
            data.email == cap.config.BASIC_AUTH_USERNAME
            and data.password == cap.config.BASIC_AUTH_PASSWORD
        ):
            return data
        return None

    @classmethod
    @webargs.query(
        dict(
            expires_access=webargs.OptField.positive(),
            expires_refresh=webargs.OptField.positive(),
        )
    )
    def access_token(cls, args):
        credentials = cls.check_credential()
        if credentials:
            return cls.handler.create(credentials, **args)
        return flask.abort(httpcode.UNAUTHORIZED)

    @classmethod
    def refresh_token(cls):
        @cls.jwt.jwt_required(refresh=True)
        def _refresh_token():
            return cls.handler.refresh()

        return _refresh_token()

    @classmethod
    def check_token(cls):
        @cls.jwt.jwt_required()
        def _check_token():
            return cls.handler.dump()

        return _check_token()

    @classmethod
    @builder.no_content
    def revoke_token(cls):
        data = flask.request.json
        if data.access_token:
            cls.handler.revoke(data.access_token)
        if data.refresh_token:
            cls.handler.revoke(data.refresh_token)

    def dispatch_request(self, *_, **__):
        if flask.request.method == HttpMethod.GET:
            return self.check_token()

        view_name = flask.request.endpoint
        if view_name.endswith("token_access"):
            return self.access_token()  # pylint: disable=no-value-for-parameter
        if view_name.endswith("token_refresh"):
            return self.refresh_token()
        if view_name.endswith("token_revoke"):
            return self.revoke_token()

        return flask.abort(httpcode.BAD_REQUEST)
