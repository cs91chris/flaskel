from flask import Blueprint

from flaskel.converters import CONVERTERS as DEFAULT_CONVERTERS
from flaskel.ext import default
from flaskel.middlewares import RequestID, HTTPMethodOverride
from flaskel.views.static import SPAView

bp_api = Blueprint(
    "api",
    __name__,
    subdomain="api",
    static_folder=None,
    static_url_path=None,
    template_folder=None,
)
bp_spa = Blueprint(
    "spa",
    __name__,
    template_folder=SPAView.default_template_folder,
    static_folder=SPAView.default_static_folder,
    static_url_path=SPAView.default_static_url_path,
)
bp_web = Blueprint(
    "web",
    __name__,
    url_prefix="/",
    template_folder="data/templates",
    static_folder="data/static",
    static_url_path="/static/",
)

default.cors.init_app(bp_api)
default.error_handler.api_register(bp_api)
default.error_handler.web_register(bp_spa)
default.error_handler.web_register(bp_web)

CONVERTERS = DEFAULT_CONVERTERS
MIDDLEWARES = (
    RequestID,
    HTTPMethodOverride,
)
BLUEPRINTS = (
    (bp_api,),
    (bp_spa,),
    (bp_web,),
)
AFTER_REQUEST = ()
BEFORE_REQUEST = ()

EXTENSIONS = {
    "cfremote": (default.cfremote,),
    "logger": (default.logger,),
    "argon2": (default.argon2,),
    "builder": (default.builder,),
    "cors": (default.cors, dict(resources={r"/*": {"origins": "*"}})),
    "database": (default.Database(),),
    "date_helper": (default.date_helper,),
    "errors": (
        default.error_handler,
        dict(
            dispatcher="subdomain",
            response=default.builder.on_accept(strict=False),
        ),
    ),
    "template": (default.template,),
    "useragent": (default.useragent,),
}
