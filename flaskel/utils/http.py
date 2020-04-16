from flask import abort, current_app as cap

from flaskel import httpcode

try:
    import requests
    http_exc = requests.exceptions
except ImportError as err:
    import warnings
    warnings.warn(str(err))
    requests = None
    http_exc = None


def filename_from_header(hdr):
    """
    get filename from Content-Disposition header.
    i.e.: attachment; filename="<file name.ext>"

    :param hdr: Content-Disposition value
    :return: only the file name
    """
    if not hdr:
        return None

    tmp = hdr.split(';')
    hdr = tmp[1] if len(tmp) > 1 else tmp[0]
    tmp = hdr.split('=')

    if len(tmp) > 1:
        return tmp[1].strip('"').lstrip('<').rstrip('>')
    else:
        return None


def dump_headers(hdr):
    """
    dumps http headers: useful for logging

    :param hdr: headers' dictionary
    :return: string representation of headers
            k1: v1
            k2: v2
    """
    return '\n'.join('{}: {}'.format(k, v) for k, v in hdr.items())


def dump_request(req):
    """
    dump http request: useful for logging

    :param req: requests' request object
    :return: prettified representation of input as string
    """
    return 'REQUEST: {} {}\nheaders:\n{}\nbody:\n{}'.format(
        req.method, req.url, dump_headers(req.headers), req.body
    )


def dump_response(resp, body=None):
    """
    dump http response: useful for logging

    :param resp: requests' response object
    :param body: flag to enable or disable dump of body response (overrides DEBUG)
    :return: prettified representation of input as string
    """
    hdr = resp.headers

    if body is None:
        body = cap.config['DEBUG']

    if body is True:
        resp_body = filename_from_header(hdr.get('Content-Disposition')) or resp.text
    else:
        resp_body = "response body not dumped"

    return 'RESPONSE status code: {}\nheaders:\n{}\nbody:\n{}'.format(
        resp.status_code, dump_headers(hdr), resp_body
    )


def request(url, method='GET', raise_on_exc=False, **kwargs):
    """

    :param method:
    :param url:
    :param raise_on_exc:
    :param kwargs:
    :return:
    """
    if requests is None:
        raise RuntimeError("requests is not installed try: pip install requests")

    if not url.startswith('http'):
        url = "http://{}".format(url)

    try:
        # noinspection PyUnresolvedReferences
        res = requests.request(method, url, **kwargs)
        cap.logger.info(dump_request(res.request))
    except (http_exc.ConnectionError, http_exc.Timeout) as exc:
        cap.logger.exception(exc)
        if raise_on_exc:
            abort(httpcode.INTERNAL_SERVER_ERROR)
            return  # only to prevent warning

        return dict(body={}, status=httpcode.SERVICE_UNAVAILABLE, headers={})

    try:
        res.raise_for_status()
    except http_exc.HTTPError as exc:
        cap.logger.warning(dump_response(res))
        res = exc.response
        if raise_on_exc:
            raise
    else:
        cap.logger.info(dump_response(res))

    try:
        body = res.json()
    except ValueError as exc:
        cap.logger.debug(str(exc))
        body = dict(content=res.text)

    return dict(
        body=body,
        status=res.status_code,
        headers=res.headers
    )
