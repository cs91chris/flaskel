import flask
from flask import current_app as cap

from . import http_status as httpcode


def get_json(allow_empty=False):
    """

    :return:
    """
    payload = flask.request.get_json()

    if not payload:
        if allow_empty:
            payload = {}
        else:
            flask.abort(httpcode.BAD_REQUEST, 'No JSON given')

    return payload


def send_file(directory, filename, **kwargs):
    """

    :param directory:
    :param filename:
    :param kwargs:
    """
    kwargs.setdefault('as_attachment', True)
    file_path = flask.safe_join(directory, filename)

    try:
        resp = flask.send_file(file_path, **kwargs)
    except IOError as exc:
        cap.logger.warning(str(exc))
        flask.abort(httpcode.NOT_FOUND)
        return  # only to prevent warning

    # following headers works with nginx compatible proxy
    if cap.use_x_sendfile is True and cap.config.get('ENABLE_ACCEL') is True:
        resp.headers['X-Accel-Redirect'] = file_path
        resp.headers['X-Accel-Charset'] = cap.config['ACCEL_CHARSET']
        resp.headers['X-Accel-Limit-Rate'] = cap.config['ACCEL_LIMIT_RATE']
        resp.headers['X-Accel-Expires'] = cap.config['SEND_FILE_MAX_AGE_DEFAULT']
        resp.headers['X-Accel-Buffering'] = 'yes' if cap.config['ACCEL_BUFFERING'] else 'no'

    return resp
