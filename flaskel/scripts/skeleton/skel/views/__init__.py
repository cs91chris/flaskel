from flaskel.extra import apidoc
from flaskel.extra.mobile_support import MobileLoggerView, MobileReleaseView
from flaskel.views import rpc
from .token import TokenAuthView

bp_api = None  # import blueprint here
rpc_service = object  # import rpc_service here
rpc.JSONRPCView.load_from_object(rpc_service())

VIEWS = (
    (TokenAuthView, bp_api),
    (rpc.JSONRPCView, bp_api),
    (apidoc.ApiDocTemplate, bp_api),
    (apidoc.ApiSpecTemplate, bp_api),
    (MobileReleaseView, bp_api),
    (MobileLoggerView, bp_api),
)
