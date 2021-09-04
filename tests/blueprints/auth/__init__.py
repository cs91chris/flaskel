# example auth blueprint
#
from flask import Blueprint

from flaskel.ext import cors, error_handler

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

cors.init_app(bp_auth)
error_handler.api_register(bp_auth)

from . import token  # noqa E402 pylint: disable=wrong-import-position
