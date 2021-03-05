from flask import Blueprint

from flaskel.ext import errors
from flaskel.views import RenderTemplate

bp_web = Blueprint(
    'web', __name__,
    template_folder="templates",
    static_folder="static"
)

errors.web_register(bp_web)
RenderTemplate.register(bp_web, url='/', name='index', template='index.html')
