from flask import abort
from flask import request

from flaskel import httpcode


def get_json():
    req = request.get_json()

    if not req:
        abort(httpcode.BAD_REQUEST, 'No JSON given')
    return req
