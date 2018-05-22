# import your blueprint here
#
from blueprints.api import api
from blueprints.web import web


BLUEPRINTS = (
    # (blueprint_name, prefix)
    (api, None),
    (web, None),
)
