# import your blueprint here
#
from .api import api
from .auth import auth
from .spa import spa
from .web import web

BLUEPRINTS = (
    # (<Blueprint>, <dict>)
    (api,),
    (spa,),
    (auth, {
        'url_prefix': '/auth'
    }),
    (web, {
        'url_prefix': '/'
    }),
)
