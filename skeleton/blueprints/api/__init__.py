# example api blueprint
#
from flask import Blueprint

from flaskel.ext import cors, errors

api = Blueprint(
    'api', __name__,
    subdomain='api',
    static_folder="static",
    static_url_path="/cdn/"
)

cors.init_app(api)
errors.api_register(api)
