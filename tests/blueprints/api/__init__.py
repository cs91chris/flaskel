from flask import Blueprint

from flaskel.ext.default import cors, errors
from flaskel.views import apidoc
from flaskel.views.proxy import ConfProxyView, TransparentProxyView
from flaskel.views.rpc import JSONRPCView
from tests.blueprints.api.resource import APIResource
from tests.blueprints.api.rpc import MyJsonRPC

api = Blueprint('api', __name__, subdomain='api')

cors.init_app(api)
errors.api_register(api)

APIResource.register(api, 'resource_api', '/resources')
apidoc.ApiDocTemplate.register(api, 'apidocs', '/apidocs')
apidoc.ApiSpecTemplate.register(api, 'apispec', '/apidoc.json')

jsonRPCView = JSONRPCView()
jsonRPCView.load_from_object(MyJsonRPC())
jsonRPCView.register(api, 'myJsonRPC', "/rpc")


class CustomProxy(TransparentProxyView):
    methods = ['POST']


CustomProxy.register(
    api, 'proxyview', '/proxy',
    host='https://httpbin.org', method='POST', url='/anything'
)

ConfProxyView.register(api, 'confproxy', '/confproxy', config_key='PROXIES.CONF')
