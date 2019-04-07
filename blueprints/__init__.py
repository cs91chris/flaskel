# import your blueprint here
#
from blueprints.api import api
from blueprints.web import web


BLUEPRINTS = (
    # (blueprint, options)
    (api,),
    (web, {
        'url_prefix': '/web'
    }),
)
