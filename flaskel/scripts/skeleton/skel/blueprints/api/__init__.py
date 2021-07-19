# example api blueprint
#
from flask import Blueprint

from flaskel.ext import cors, error_handler

bp_api = Blueprint(
    "api", __name__, subdomain="api", static_folder="static", static_url_path="/cdn/"
)

cors.init_app(bp_api)
error_handler.api_register(bp_api)
