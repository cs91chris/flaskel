# example web blueprint
#
from flask import Blueprint

from flaskel.ext import errors
from flaskel.views import RenderTemplate

web = Blueprint(
    'web', __name__,
    template_folder="templates",
    static_folder="static"
)

errors.web_register(web)
RenderTemplate.register(web, url='/', name='index', template='index.html')
