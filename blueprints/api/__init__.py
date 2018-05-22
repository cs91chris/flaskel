# example api blueprint
#

from flask import Blueprint

api = Blueprint('api', __name__, subdomain='api')

from . import index
