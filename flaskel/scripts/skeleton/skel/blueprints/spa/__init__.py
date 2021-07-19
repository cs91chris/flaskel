# example spa blueprint
#
import os

from flask import Blueprint

from flaskel import cap
from flaskel.ext import error_handler

static_folder = os.environ.get("SPA_STATIC_FOLDER") or "webapp"
static_url_path = os.environ.get("SPA_STATIC_URL_PATH") or "/assets/"

bp_spa = Blueprint(
    "spa", __name__, static_folder=static_folder, static_url_path=static_url_path
)

error_handler.web_register(bp_spa)


@bp_spa.route("/", defaults=dict(path=""))
@bp_spa.route("/<path:path>")
def catch_all(path):
    """

    :param path:
    :return:
    """
    return cap.send_static_file("index.html")
