import flask
from flaskel import httpcode


def get_json():
    """

    :return:
    """
    req = flask.request.get_json()

    if not req:
        flask.abort(httpcode.BAD_REQUEST, 'No JSON given')
    return req
