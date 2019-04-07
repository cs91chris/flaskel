# import your blueprint here
#
from blueprints.api import api
from blueprints.web import web


BLUEPRINTS = (
    # (blueprint_name, options)
    (api, {
        'subdomain': 'api'
    }),
    (web, {
        'url_prefix': '/web'
    }),
)
