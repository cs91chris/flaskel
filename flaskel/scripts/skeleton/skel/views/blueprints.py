from flask import Blueprint

from flaskel.ext.default import cors, error_handler
from flaskel.views.static import SPAView

bp_api = Blueprint(
    "api",
    __name__,
    subdomain="api",
    static_folder=None,
    static_url_path=None,
    template_folder=None,
)

bp_auth = Blueprint(
    "auth",
    __name__,
    subdomain="api",
    url_prefix="/auth",
    static_folder=None,
    static_url_path=None,
    template_folder=None,
)

bp_spa = Blueprint(
    "spa",
    __name__,
    url_prefix="/",
    template_folder=SPAView.default_template_folder,
    static_folder=SPAView.default_static_folder,
    static_url_path=SPAView.default_static_url_path,
)

bp_web = Blueprint(
    "web",
    __name__,
    url_prefix="/",
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/",
)


cors.init_app(bp_api)
cors.init_app(bp_auth)
error_handler.api_register(bp_api)
error_handler.api_register(bp_auth)
error_handler.web_register(bp_spa)
error_handler.web_register(bp_web)
