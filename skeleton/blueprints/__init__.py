# import your blueprint here
#
from .api import api
from .web import web


BLUEPRINTS = (
    # (blueprint, options)
    (api,),
    (web, {
        'url_prefix': '/'
    }),
)
