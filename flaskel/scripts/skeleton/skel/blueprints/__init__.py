from .api import bp_api
from .auth import bp_auth
from .web import bp_web

BLUEPRINTS = (
    (bp_api,),
    (bp_web, {"url_prefix": "/"}),
    (bp_auth, {"url_prefix": "/auth"}),
)

VIEWS = (
    # (view, blueprint, dict options)
)
