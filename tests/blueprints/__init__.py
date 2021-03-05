from .api import bp_api
from .auth import bp_auth
from .test import bp_test
from .web import bp_web

BLUEPRINTS = (
    (bp_api,),
    (bp_test,),
    (bp_web, {
        'url_prefix': '/'
    }),
    (bp_auth, {
        'url_prefix': '/auth'
    }),
)
