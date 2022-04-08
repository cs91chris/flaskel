import flask_jwt_extended
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod

from flaskel import abort, cap, request, webargs
from flaskel.ext.auth import BaseTokenHandler
from flaskel.ext.default import builder
from flaskel.views import BaseView
from flaskel.views.base import UrlRule


class BaseTokenAuth(BaseView):
    jwt = flask_jwt_extended
    handler: BaseTokenHandler = BaseTokenHandler()

    default_view_name = "token_auth"
    methods = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    """
        NOTE: endpoint should not be change otherwise dispatch_request MUST change
    """
    default_urls = (
        UrlRule(url="/token/access", endpoint="token_access"),
        UrlRule(url="/token/refresh", endpoint="token_refresh"),
        UrlRule(url="/token/revoke", endpoint="token_revoke"),
        UrlRule(url="/token/check", endpoint="token_check"),
    )

    @classmethod
    def check_credential(cls):
        data = request.json
        if (
            data.email == cap.config.ADMIN_EMAIL
            and data.password == cap.config.ADMIN_PASSWORD
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
    def access_token(cls, args) -> ObjectDict:
        credentials = cls.check_credential()
        if credentials:
            return cls.handler.create(credentials, **args).to_dict()
        return abort(httpcode.UNAUTHORIZED)

    @classmethod
    def refresh_token(cls) -> ObjectDict:
        @cls.jwt.jwt_required(refresh=True)
        def _refresh_token():
            return cls.handler.refresh().to_dict()

        return _refresh_token()

    @classmethod
    def check_token(cls):
        @cls.jwt.jwt_required()
        def _check_token():
            return cls.handler.dump().to_dict()

        return _check_token()

    @classmethod
    @builder.no_content
    def revoke_token(cls):
        data = request.json
        if data.access_token:
            cls.handler.revoke(data.access_token)
        if data.refresh_token:
            cls.handler.revoke(data.refresh_token)

    def dispatch_request(self, *_, **__):
        if request.method == HttpMethod.GET:
            return self.check_token()

        view_name = request.endpoint
        if view_name.endswith("token_access"):
            return self.access_token()  # pylint: disable=no-value-for-parameter
        if view_name.endswith("token_refresh"):
            return self.refresh_token()
        if view_name.endswith("token_revoke"):
            return self.revoke_token()

        return abort(httpcode.BAD_REQUEST)
