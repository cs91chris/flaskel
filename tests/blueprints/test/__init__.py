# example api blueprint
#
from flask import Blueprint

test = Blueprint(
    'test',
    __name__
)

from . import index
