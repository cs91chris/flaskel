# example api blueprint
#
from flask import Blueprint

from flaskel.ext import cors, errors

api = Blueprint('api', __name__, subdomain='api')

cors.init_app(api)
errors.api_register(api)
