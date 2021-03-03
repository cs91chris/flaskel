# example web blueprint
#
from flask import Blueprint

from flaskel.ext.default import errors
from flaskel.views.template import RenderTemplate

bp_web = Blueprint(
    'web', __name__,
    url_prefix='/',
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/"
)

errors.web_register(bp_web)
RenderTemplate.register(bp_web, url='/', name='index', template='index.html')
