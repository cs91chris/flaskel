# import your blueprint here
#
from .api import api
from .web import web
from .spa import spa

BLUEPRINTS = (
    # (<Blueprint>, <dict>)
    (api,),
    (spa,),
    (web, {
        'url_prefix': '/'
    }),
)
