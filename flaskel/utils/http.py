def dump_request(req):
    """
    dump http request: useful for logging

    :param req: requests' request object
    :return: prettified representation of input as string
    """
    headers = req.headers.items()
    return 'REQUEST: {} {}\nheaders:\n{}\nbody:\n{}'.format(
        req.method,
        req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in headers),
        req.body
    )


def dump_response(resp):
    """
    dump http response: useful for logging

    :param resp: requests' response object
    :return: prettified representation of input as string
    """
    hdr = 'Content-Disposition'
    headers = resp.headers.items()

    return 'RESPONSE status code: {}\nheaders:\n{}\nbody:\n{}'.format(
        resp.status_code,
        '\n'.join('{}: {}'.format(k, v) for k, v in headers),
        filename_from_header(resp.headers[hdr]) if hdr in resp.headers.keys() else resp.text
    )
