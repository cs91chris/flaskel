from flaskel import client_redis
from flaskel.ext.auth import basic_auth, RedisTokenHandler
from flaskel.ext.default import caching
from flaskel.ext.limit import RateLimit
from flaskel.extra import apidoc, mobile_support as mobile
from flaskel.extra.account import (
    PasswordForgotView as BasePasswordForgotView,
    PasswordResetView as BasePasswordResetView,
    RegisterView as BaseRegisterView,
)
from flaskel.views import Resource
from flaskel.views.token import BaseTokenAuth

from ..ext.auth import token_handler


class TokenAuthView(BaseTokenAuth):
    handler = RedisTokenHandler(client_redis)

    @classmethod
    def check_credential(cls):
        raise NotImplementedError("implement me!")


class ApiDocTemplate(apidoc.ApiDocTemplate):
    decorators = [
        caching.cached(),
        basic_auth.login_required(),
    ]


class ApiSpecTemplate(apidoc.ApiSpecTemplate):
    decorators = [
        caching.cached(),
        basic_auth.login_required(),
    ]


class MobileReleaseView(mobile.MobileReleaseView):
    decorators = [
        token_handler.auth_required(),
    ]


class MobileLoggerView(mobile.MobileLoggerView):
    decorators = [
        token_handler.auth_required(),
    ]


class RegisterView(BaseRegisterView):
    decorators = [
        RateLimit.slow(),
    ]


class PasswordForgotView(BasePasswordForgotView):
    decorators = [
        RateLimit.slow(),
    ]


class PasswordResetView(BasePasswordResetView):
    decorators = [
        token_handler.auth_required(),
    ]


class ApiCatalog(Resource):
    methods_subresource = None

    decorators = [
        caching.cached(),
        token_handler.auth_required(),
    ]
