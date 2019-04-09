import uuid

from flask import abort
from flask import request
from flask import current_app as cap

from flaskel import httpcode


def get_json():
    req = request.get_json()

    if not req:
        abort(httpcode.BAD_REQUEST, 'No JSON given')
    return req


def get_uuid(ver=4, ns=None, name=None):
    if ver == 1:
        return uuid.uuid1().hex
    if ver == 3:
        return uuid.uuid3(
            ns or uuid.NAMESPACE_DNS, name or cap.config['SERVER_NAME']
        ).hex
    if ver == 4:
        return uuid.uuid4().hex
    if ver == 5:
        return uuid.uuid5(
            ns or uuid.NAMESPACE_DNS, name or cap.config['SERVER_NAME']
        ).hex


def check_uuid(u: str, ver=4, exc=False):
    try:
        return str(u) == str(uuid.UUID(str(u), version=ver))
    except (ValueError, TypeError, AttributeError):
        if exc:
            raise ValueError("'{}' is an invalid UUID{}".format(str(u), ver))
        return False
