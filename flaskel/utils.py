import uuid

from flask import abort
from flask import request
from flask import current_app as cap

from flaskel import httpcode


def get_json():
    """

    :return:
    """
    req = request.get_json()

    if not req:
        abort(httpcode.BAD_REQUEST, 'No JSON given')
    return req


def get_uuid(ver=4, hexify=True, ns=None, name=None):
    """

    :param ver:
    :param hexify:
    :param ns:
    :param name:
    :return:
    """
    _uuid = None

    if ver == 1:
        _uuid = uuid.uuid1()
    elif ver == 3:
        _uuid = uuid.uuid3(
            ns or uuid.NAMESPACE_DNS, name or cap.config['SERVER_NAME']
        )
    elif ver == 4:
        _uuid = uuid.uuid4()
    elif ver == 5:
        _uuid = uuid.uuid5(
            ns or uuid.NAMESPACE_DNS, name or cap.config['SERVER_NAME']
        )

    return _uuid.hex if hexify else _uuid


def check_uuid(u: str, ver=4, exc=False):
    """

    :param u:
    :param ver:
    :param exc:
    :return:
    """
    try:
        if isinstance(u, uuid.UUID):
            return True

        _uuid = uuid.UUID(u, version=ver)
        return u == (str(_uuid) if '-' in u else _uuid.hex)
    except (ValueError, TypeError, AttributeError):
        if exc:
            raise ValueError("'{}' is an invalid UUID{}".format(str(u), ver))
        return False
