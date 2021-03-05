# example auth blueprint
#
from flask import Blueprint

from flaskel.ext import cors, errors

bp_auth = Blueprint('auth', __name__, url_prefix='/auth')

cors.init_app(bp_auth)
errors.api_register(bp_auth)

from . import token
