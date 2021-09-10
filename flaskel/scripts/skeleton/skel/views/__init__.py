from flaskel.extra import apidoc
from flaskel.extra.mobile_support import MobileLoggerView, MobileReleaseView
from flaskel.views import rpc
from .blueprints import bp_auth, bp_api
from .token import TokenAuthView

rpc_service = object  # import rpc_service here
rpc.JSONRPCView.load_from_object(rpc_service())

BLUEPRINTS = (
    (bp_api,),
    (bp_auth, {"url_prefix": "/auth"}),
)

VIEWS = (
    (TokenAuthView, bp_auth),
    (rpc.JSONRPCView, bp_api),
    (apidoc.ApiDocTemplate, bp_api),
    (apidoc.ApiSpecTemplate, bp_api),
    (MobileReleaseView, bp_api),
    (MobileLoggerView, bp_api),
)
