class HTTPDumper:
    @classmethod
    def dump_headers(cls, hdr):
        """
        dumps http headers: useful for logging

        :param hdr: headers' dictionary
        :return: string representation of headers
                k1: v1
                k2: v2
        """
        return '\n'.join('{}: {}'.format(k, v) for k, v in hdr.items())

    @classmethod
    def response_filename(cls, headers):
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

    @classmethod
    def dump_request(cls, req, dump_body=None):
        """
        dump http request: useful for logging

        :param req: Request instance
        :param dump_body: flag to enable or disable dump of request's body (overrides default)
        :return: prettified representation of input as string
        """
        if dump_body is True:
            body = req.body or "empty body"
            if type(body) is not str:
                body = body.decode()
        else:
            body = "request body not dumped"

        headers = cls.dump_headers(req.headers)
        return f"{req.method} {req.url}\nheaders:\n{headers}\nbody:\n{body}"

    @classmethod
    def dump_response(cls, response, dump_body=None):
        """
        dump http response: useful for logging

        :param response: Response instance
        :param dump_body: flag to enable or disable dump of response's body (overrides default)
        :return: prettified representation of input as string
        """
        resp = response
        hdr = resp.headers

        if dump_body is True:
            body = cls.response_filename(resp.headers) or resp.text
            if type(body) is not str:
                body = body.decode()
        else:
            body = "response body not dumped"

        try:
            seconds = resp.elapsed.total_seconds()
        except AttributeError:  # because aiohttp.ClientResponse has not elapsed attribute
            seconds = 'N/A'

        headers = cls.dump_headers(hdr)
        status = resp.status_code if hasattr(resp, 'status_code') else resp.status
        return f"time : {seconds} - status code: {status}\nheaders:\n{headers}\nbody:\n{body}"
