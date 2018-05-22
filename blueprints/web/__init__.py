# example web blueprint
#

from flask import Blueprint

from flaskel.ext import errors


web = Blueprint(
    'web', __name__,
    template_folder="templates",
    static_folder="static"
)

errors.web_register(web)


from . import index
