# example api blueprint
#
from flask import Blueprint

api = Blueprint(
    'api',
    __name__,
    subdomain='api'
)

from . import index

from flaskel.ext import cors
from flaskel.ext import errors


cors.init_app(api)
errors.api_register(api)
