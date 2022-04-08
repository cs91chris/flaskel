from flaskel.views import rpc

from .blueprints import bp_api, bp_auth, bp_spa, bp_web
from .common import (
    ApiDocTemplate,
    ApiSpecTemplate,
    MobileLoggerView,
    MobileReleaseView,
    PasswordForgotView,
    PasswordResetView,
    RegisterView,
    TokenAuthView,
)

rpc_service = object  # import rpc_service here
rpc.JSONRPCView.load_from_object(rpc_service())

BLUEPRINTS = (
    (bp_spa,),
    (bp_api, {"subdomain": bp_api.subdomain}),
    (bp_web, {"url_prefix": bp_web.url_prefix}),
    (bp_auth, {"url_prefix": bp_auth.url_prefix}),
)

VIEWS = (
    (TokenAuthView, bp_auth),
    (RegisterView, bp_auth),
    (PasswordResetView, bp_auth),
    (PasswordForgotView, bp_auth),
    (rpc.JSONRPCView, bp_api),
    (ApiDocTemplate, bp_api),
    (ApiSpecTemplate, bp_api),
    (MobileReleaseView, bp_api),
    (MobileLoggerView, bp_api),
)
