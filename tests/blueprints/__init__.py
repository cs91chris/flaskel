from flaskel import ExtProxy
from flaskel.extra.mobile_support import MobileLoggerView, MobileReleaseView
from flaskel.views import proxy, RenderTemplate, rpc
from flaskel.extra import apidoc
from . import models, views
from .api import bp_api, resource, rpc as rpc_service
from .auth import bp_auth
from .test import bp_test
from .web import bp_web

jsonRPCView = rpc.JSONRPCView
rpc.JSONRPCView.load_from_object(rpc_service.MyJsonRPC())
session = ExtProxy("sqlalchemy.db.session")


class CustomProxy(proxy.TransparentProxyView):
    methods = ["POST"]


BLUEPRINTS = (
    (bp_api,),
    (bp_test,),
    (bp_web, {"url_prefix": "/"}),
    (bp_auth, {"url_prefix": "/auth"}),
)

VIEWS = (
    (RenderTemplate, bp_web, dict(name="index", urls=["/"], template="index.html")),
    (
        proxy.ConfProxyView,
        bp_api,
        dict(name="confproxy", urls=["/confproxy"], config_key="PROXIES.CONF"),
    ),
    (
        CustomProxy,
        bp_api,
        dict(
            name="proxyview",
            urls=["/proxy"],
            method="POST",
            host="https://httpbin.org",
            url="/anything",
        ),
    ),
    (resource.APIResource, bp_api, dict(name="resource_api", url="/resources")),
    (
        jsonRPCView,
        bp_api,
        dict(name=jsonRPCView.default_view_name, url=jsonRPCView.default_url),
    ),
    (
        apidoc.ApiDocTemplate,
        bp_api,
        dict(
            name=apidoc.ApiDocTemplate.default_view_name,
            urls=apidoc.ApiDocTemplate.default_urls,
        ),
    ),
    (
        apidoc.ApiSpecTemplate,
        bp_api,
        dict(
            name=apidoc.ApiSpecTemplate.default_view_name,
            urls=apidoc.ApiSpecTemplate.default_urls,
        ),
    ),
    (
        MobileReleaseView,
        bp_api,
        dict(
            name=MobileReleaseView.default_view_name,
            urls=MobileReleaseView.default_urls,
        ),
    ),
    (
        MobileLoggerView,
        bp_api,
        dict(
            name=MobileLoggerView.default_view_name,
            urls=MobileLoggerView.default_urls,
        ),
    ),
    (views.ApiItem, bp_api, dict(name="items", model=models.Dummy, session=session)),
    (
        proxy.SchemaProxyView,
        bp_api,
        dict(name="schema_proxy", urls=proxy.SchemaProxyView.default_urls),
    ),
)
