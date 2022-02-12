from flask import Blueprint

from flaskel.extra import apidoc
from flaskel.extra.mobile_support import MobileLoggerView, MobileReleaseView
from flaskel.utils.datastruct import ExtProxy
from flaskel.views import proxy, RenderTemplate, rpc
from flaskel.views.proxy import JsonRPCProxy
from . import models, views
from .endpoints import bp_test
from .views import TokenAuthView, APIResource, MyJsonRPC
from .web import bp_web

bp_api = Blueprint("api", __name__)


JsonRPCView = rpc.JSONRPCView
rpc.JSONRPCView.load_from_object(MyJsonRPC())
session = ExtProxy("sqlalchemy.db.session")


class CustomProxy(proxy.TransparentProxyView):
    methods = ["POST"]
    default_view_name = "proxyview"
    default_urls = ("/proxy",)


BLUEPRINTS = (
    (bp_api,),
    (bp_test,),
    (bp_web, {"url_prefix": "/"}),
)

VIEWS = (
    (TokenAuthView, bp_api),
    (apidoc.ApiDocTemplate, bp_api),
    (apidoc.ApiSpecTemplate, bp_api),
    (MobileReleaseView, bp_api),
    (MobileLoggerView, bp_api),
    (proxy.SchemaProxyView, bp_api),
    (JsonRPCView, bp_api),
    (RenderTemplate, bp_web),
    (
        proxy.ConfProxyView,
        bp_api,
        dict(name="confproxy", config_key="PROXIES.CONF"),
    ),
    (
        CustomProxy,
        bp_api,
        dict(
            method="POST",
            host="https://httpbin.org",
            url="/anything",
        ),
    ),
    (
        APIResource,
        bp_api,
        dict(name="resource_api", urls=("/resources",)),
    ),
    (
        views.ApiItem,
        bp_api,
        dict(name="items", model=models.Dummy, session=session),
    ),
    (
        JsonRPCProxy,
        bp_api,
        dict(
            urls=("/jsonrpc_method",),
            name="jsonrpc_proxyview",
            host="https://httpbin.org/anything",
        ),
    ),
)
