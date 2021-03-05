from flask import Blueprint

from flaskel.ext import cors, errors
from flaskel.views import apidoc
from flaskel.views.proxy import ConfProxyView, TransparentProxyView
from flaskel.views.rpc import JSONRPCView
from tests.blueprints.api.resource import APIResource
from tests.blueprints.api.rpc import MyJsonRPC

bp_api = Blueprint('api', __name__, subdomain='api')

cors.init_app(bp_api)
errors.api_register(bp_api)

APIResource.register(bp_api, 'resource_api', '/resources')
apidoc.ApiDocTemplate.register(bp_api, 'apidocs', '/apidocs')
apidoc.ApiSpecTemplate.register(bp_api, 'apispec', '/apidoc.json')

jsonRPCView = JSONRPCView()
jsonRPCView.load_from_object(MyJsonRPC())
jsonRPCView.register(bp_api, 'myJsonRPC', "/rpc")


class CustomProxy(TransparentProxyView):
    methods = ['POST']


CustomProxy.register(
    bp_api, 'proxyview', '/proxy',
    host='https://httpbin.org', method='POST', url='/anything'
)

ConfProxyView.register(bp_api, 'confproxy', '/confproxy', config_key='PROXIES.CONF')
