from .api import api
from .auth import auth
from .test import test
from .web import web

BLUEPRINTS = (
    (api,),
    (test,),
    (web, {
        'url_prefix': '/'
    }),
    (auth, {
        'url_prefix': '/auth'
    }),
)
