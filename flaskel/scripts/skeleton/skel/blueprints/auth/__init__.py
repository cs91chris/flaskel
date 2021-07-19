# example auth blueprint
#
from flask import Blueprint

from flaskel.ext import cors, error_handler

bp_auth = Blueprint("auth", __name__, subdomain="api", url_prefix="/auth")

cors.init_app(bp_auth)
error_handler.api_register(bp_auth)
