# import your blueprint here
#
from .api import api
from .web import web

BLUEPRINTS = (
    # (<Blueprint>, <dict>)
    (api,),
    (web, {
        'url_prefix': '/'
    }),
)
