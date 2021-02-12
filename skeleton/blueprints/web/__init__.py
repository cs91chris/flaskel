# example web blueprint
#
from flask import Blueprint

from flaskel.ext import errors
from flaskel.views import RenderTemplate

web = Blueprint(
    'web', __name__,
    url_prefix='/',
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/"
)

errors.web_register(web)
RenderTemplate.register(web, url='/', name='index', template='index.html')
