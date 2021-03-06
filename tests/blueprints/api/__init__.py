from flask import Blueprint

from flaskel.ext import cors, errors

bp_api = Blueprint('api', __name__, subdomain='api')

cors.init_app(bp_api)
errors.api_register(bp_api)
