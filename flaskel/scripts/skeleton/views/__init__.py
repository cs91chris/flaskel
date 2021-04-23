from flaskel.extra.mobile_support import MobileLoggerView, MobileReleaseView
from flaskel.views import apidoc, rpc

bp_api = None  # import blueprint here
rpc_service = object  # import rpc_service here
rpc.JSONRPCView.load_from_object(rpc_service())

VIEWS = (
    (rpc.JSONRPCView, dict(
        name=rpc.JSONRPCView.default_view_name,
        url=rpc.JSONRPCView.default_url
    )),
    (apidoc.ApiDocTemplate, bp_api, dict(
        name=apidoc.ApiDocTemplate.default_view_name,
        urls=apidoc.ApiDocTemplate.default_urls
    )),
    (apidoc.ApiSpecTemplate, bp_api, dict(
        name=apidoc.ApiSpecTemplate.default_view_name,
        urls=apidoc.ApiSpecTemplate.default_urls
    )),
    (MobileReleaseView, bp_api, dict(
        name=MobileReleaseView.default_view_name,
        urls=MobileReleaseView.default_urls,
    )),
    (MobileLoggerView, bp_api, dict(
        name=MobileLoggerView.default_view_name,
        urls=MobileLoggerView.default_urls,
    )),
)
