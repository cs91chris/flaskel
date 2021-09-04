from flask import Blueprint

bp_test = Blueprint("test", __name__)

from . import index  # noqa E402 pylint: disable=wrong-import-position
