from flask import Blueprint

from flaskel.ext import cors, errors
from flaskel.views import JSONRPCView, TransparentProxyView, ConfProxyView
from tests.blueprints.api.resource import APIResource
from tests.blueprints.api.rpc import MyJsonRPC

api = Blueprint('api', __name__, subdomain='api')

cors.init_app(api)
errors.api_register(api)

APIResource.register(api, 'resource_api', '/resources')

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
