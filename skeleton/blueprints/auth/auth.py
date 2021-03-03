# example auth blueprint
#
from flask import Blueprint

from flaskel.ext.default import cors, errors

bp_auth = Blueprint('auth', __name__, subdomain='api', url_prefix='/auth')

cors.init_app(bp_auth)
errors.api_register(bp_auth)
