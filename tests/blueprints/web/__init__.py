from flask import Blueprint

web = Blueprint(
    'web', __name__,
    template_folder="templates",
    static_folder="templates"
)

from flaskel.ext import errors
errors.web_register(web)


from . import index
