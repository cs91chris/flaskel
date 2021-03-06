from flaskel import views
from flaskel.views import apidoc, proxy, rpc
from .api import bp_api, resource, rpc as rpcserice
from .auth import bp_auth
from .test import bp_test
from .web import bp_web

jsonRPCView = rpc.JSONRPCView
rpc.JSONRPCView.load_from_object(rpcserice.MyJsonRPC())


class CustomProxy(proxy.TransparentProxyView):
    methods = ['POST']


BLUEPRINTS = (
    (bp_api,),
    (bp_test,),
    (bp_web, {
        'url_prefix': '/'
    }),
    (bp_auth, {
        'url_prefix': '/auth'
    }),
)

VIEWS = (
    (views.RenderTemplate, bp_web, dict(
        name='index',
        urls=['/'],
        template='index.html'
    )),
    (proxy.ConfProxyView, bp_api, dict(
        name='confproxy',
        urls=['/confproxy'],
        config_key='PROXIES.CONF'
    )),
    (CustomProxy, bp_api, dict(
        name='proxyview',
        urls=['/proxy'],
        method='POST',
        host='https://httpbin.org',
        url='/anything'
    )),
    (jsonRPCView, dict(
        name='myJsonRPC',
        url="/rpc"
    )),
    (apidoc.ApiDocTemplate, bp_api, dict(
        name='apidocs',
        urls=['/apidocs']
    )),
    (apidoc.ApiSpecTemplate, bp_api, dict(
        name='apispec',
        urls=['/apidoc.json']
    )),
    (resource.APIResource, bp_api, dict(
        name='resource_api',
        url='/resources'
    )),
)
