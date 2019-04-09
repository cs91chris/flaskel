# example api blueprint
#
from flask import Blueprint

api = Blueprint(
    'api',
    __name__,
    subdomain='api'
)

from ext import errors
errors.api_register(api)


from . import index
