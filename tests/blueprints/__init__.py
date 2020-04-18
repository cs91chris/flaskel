from .api import api
from .web import web
from .test import test

BLUEPRINTS = (
    (api,),
    (test,),
    (web, {
        'url_prefix': '/'
    }),
)
