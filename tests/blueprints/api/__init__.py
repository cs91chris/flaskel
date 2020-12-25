from flask import Blueprint

from flaskel.ext import cors, errors
from flaskel.views import JSONRPCView
from tests.blueprints.api.resource import APIResource
from tests.blueprints.api.rpc import MyJsonRPC

api = Blueprint('api', __name__, subdomain='api')

cors.init_app(api)
errors.api_register(api)

APIResource.register(api, 'resource_api', '/resources')

jsonRPCView = JSONRPCView()
jsonRPCView.load_from_object(MyJsonRPC())
jsonRPCView.register(api, 'myJsonRPC', "/rpc")
