from flask import Blueprint

from flaskel.ext import error_handler

bp_web = Blueprint("web", __name__, template_folder="templates", static_folder="static")

error_handler.web_register(bp_web)
