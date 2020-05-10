import flask
from flaskel import cap

from . import http_status as httpcode


def get_json(allow_empty=False):
    """

    :param allow_empty:
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


def dump_headers(hdr):
    """
    dumps http headers: useful for logging

    :param hdr: headers' dictionary
    :return: string representation of headers
            k1: v1
            k2: v2
    """
    return '\n'.join('{}: {}'.format(k, v) for k, v in hdr.items())


def dump_request(req, dump_body=None):
    """
    dump http request: useful for logging

    :param req: Request instance
    :param dump_body: flag to enable or disable dump of request's body (overrides default)
    :return: prettified representation of input as string
    """
    if dump_body is True:
        req_body = req.body
    else:
        req_body = "request body not dumped"

    return 'REQUEST: {} {}\nheaders:\n{}\nbody:\n{}'.format(
        req.method, req.url, dump_headers(req.headers), req_body
    )


def dump_response(response, dump_body=None):
    """
    dump http response: useful for logging

    :param response: Response instance
    :param dump_body: flag to enable or disable dump of response's body (overrides default)
    :return: prettified representation of input as string
    """
    resp = response
    hdr = resp.headers

    if dump_body is True:
        resp_body = get_response_filename(resp.headers) or resp.text
    else:
        resp_body = "response body not dumped"

    status_code = resp.status_code if hasattr(resp, 'status_code') else resp.status

    return 'RESPONSE status code: {}\nheaders:\n{}\nbody:\n{}'.format(
        status_code, dump_headers(hdr), resp_body
    )


def get_response_filename(headers):
    """
    get filename from Content-Disposition header.
    i.e.: attachment; filename="<file name.ext>"

    :param headers: http headers dict
    :return: only the file name
    """
    hdr = headers.get('Content-Disposition')
    if not hdr:
        return None

    tmp = hdr.split(';')
    hdr = tmp[1] if len(tmp) > 1 else tmp[0]
    tmp = hdr.split('=')

    if len(tmp) > 1:
        return tmp[1].strip('"').lstrip('<').rstrip('>')
    else:
        return None
