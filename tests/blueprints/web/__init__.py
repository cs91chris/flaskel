from flask import Blueprint

from flaskel.ext import errors

bp_web = Blueprint(
    'web', __name__,
    template_folder="templates",
    static_folder="static"
)

errors.web_register(bp_web)
