# example auth blueprint
#
from flask import Blueprint

from flaskel.ext import cors, errors

auth = Blueprint('auth', __name__, subdomain='api', url_prefix='/auth')

cors.init_app(auth)
errors.api_register(auth)
