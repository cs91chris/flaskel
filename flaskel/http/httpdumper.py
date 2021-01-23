from flask import current_app as cap


class HTTPDumper:
    @staticmethod
    def padding(text):
        """

        :param text:
        :return:
        """
        return "\n{}".format(text)

    @classmethod
    def dump_headers(cls, hdr, only=()):
        """
        dumps http headers: useful for logging

        :param hdr: headers' dictionary
        :param only: list of headers key to dump
        :return: string representation of headers
                k1: v1
                k2: v2
        """
        if only:
            hdr = {k: hdr[k] for k in only if k in hdr}

        return cls.padding('\n'.join('{}: {}'.format(k, v) for k, v in hdr.items()))

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
            return None  # pragma: no cover

        tmp = hdr.split(';')
        hdr = tmp[1] if len(tmp) > 1 else tmp[0]
        tmp = hdr.split('=')

        if len(tmp) > 1:
            return tmp[1].strip('"').lstrip('<').rstrip('>')
        else:
            return None

    @classmethod
    def dump_request(cls, req, dump_body=None, only_hdr=()):
        """
        dump http request: useful for logging

        :param req: Request instance
        :param dump_body: flag to enable or disable dump of request's body (overrides default)
        :param only_hdr: dump only a subset of headers
        :return: prettified representation of input as string
        """
        body = None
        if dump_body is True:
            try:
                body = req.body or "empty body"
                if type(body) is not str:
                    body = body.decode()
            except AttributeError as exc:
                body = str(exc)
        if body:
            body = f"body:\n{body}"

        headers = cls.dump_headers(req.headers, only=only_hdr)
        if headers:
            headers = f"headers:\n{headers}\n"

        return f"{req.method} {req.url}\n{headers}{body}"

    @classmethod
    def dump_response(cls, resp, dump_body=None, only_hdr=()):
        """
        dump http response: useful for logging

        :param resp: Response instance
        :param dump_body: flag to enable or disable dump of response's body (overrides default)
        :param only_hdr: dump only a subset of headers
        :return: prettified representation of input as string
        """
        body = None
        if dump_body is True:
            body = cls.response_filename(resp.headers) or resp.text
            try:
                if type(body) is not str:
                    body = body.decode()
            except AttributeError as exc:
                body = str(exc)

        try:
            seconds = resp.elapsed.total_seconds()
        except AttributeError:  # because aiohttp.ClientResponse has not elapsed attribute
            seconds = 'N/A'

        if body:
            body = f"body:\n{body}"

        headers = cls.dump_headers(resp.headers, only=only_hdr)
        if headers:
            headers = f"headers:\n{headers}\n"
        status = resp.status_code if hasattr(resp, 'status_code') else resp.status
        return f"time : {seconds} - status code: {status}\n{headers}{body}"


class FlaskelHTTPDumper:
    @classmethod
    def dump_request(cls, req, dump_body=None):
        return HTTPDumper.dump_request(
            req, dump_body, only_hdr=cap.config.LOG_REQ_HEADERS
        )

    @classmethod
    def dump_response(cls, resp, dump_body=None):
        return HTTPDumper.dump_response(
            resp, dump_body, only_hdr=cap.config.LOG_RESP_HEADERS
        )
