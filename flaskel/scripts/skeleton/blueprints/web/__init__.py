# example web blueprint
#
from flask import Blueprint

from flaskel.ext import errors
from flaskel.views import RenderTemplate

bp_web = Blueprint(
    'web', __name__,
    url_prefix='/',
    template_folder="templates",
    static_folder="static",
    static_url_path="static/"
)

errors.web_register(bp_web)
RenderTemplate.register(bp_web, name='index', urls=['/'], template='index.html')
