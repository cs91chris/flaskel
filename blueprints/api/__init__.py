# example api blueprint
#
from flask import Blueprint

api = Blueprint(
    'api',
    __name__,
    subdomain='api'
)

from . import index

from ext import errors
from ext import cors


cors.init_app(api)
errors.api_register(api)
