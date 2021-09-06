from .api import bp_api
from .web import bp_web

BLUEPRINTS = (
    (bp_api,),
    (bp_web, {"url_prefix": "/"}),
)

VIEWS = (
    # (view, blueprint, dict options)
)
