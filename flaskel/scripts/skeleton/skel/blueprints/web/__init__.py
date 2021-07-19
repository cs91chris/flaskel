# example web blueprint
#
from flask import Blueprint

from flaskel.ext import error_handler
from flaskel.views import RenderTemplate

bp_web = Blueprint(
    "web",
    __name__,
    url_prefix="/",
    template_folder="templates",
    static_folder="static",
    static_url_path="static/",
)

error_handler.web_register(bp_web)
RenderTemplate.register(bp_web, name="index", urls=["/"], template="index.html")
