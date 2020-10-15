from werkzeug.urls import url_decode
from werkzeug.middleware.proxy_fix import ProxyFix


class ForceHttps(object):
    """
    NOTE: use this only if you can not touch reverse proxy configuration
    use ReverseProxied instead
    """
    def __init__(self, app):
        """

        :param app:
        """
        self._app = app

    def __call__(self, environ, start_response):
        """

        :param environ:
        :param start_response:
        :return:
        """
        environ['wsgi.url_scheme'] = 'https'
        return self._app(environ, start_response)


class ReverseProxied(ProxyFix):
    """
    adjust the WSGI environ based on X-Forwarded- that proxies in
    front of the application may set:

    -   X-Forwarded-For    -> sets REMOTE_ADDR
    -   X-Forwarded-Proto  -> sets wsgi.url_scheme
    -   X-Forwarded-Host   -> sets HTTP_HOST, SERVER_NAME, and SERVER_PORT
    -   X-Forwarded-Port   -> sets HTTP_HOST and SERVER_PORT
    -   X-Forwarded-Prefix -> sets SCRIPT_NAME

    for example nginx:
        location /prefix {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarder-Proto $proto;
            proxy_set_header X-Forwarder-Port 5000;
            proxy_set_header X-Forwarder-Prefix /prefix;
        }

    You must tell the middleware how many proxies set each header so it
    knows what values to trust. It is a security issue to trust values
    that came from the client rather than a proxy.

    The original values of the headers are stored in the WSGI
    environ as werkzeug.proxy_fix.orig, a dict.
    """
    def __init__(self, app, x_for=1, x_proto=1, x_host=1, x_port=0, x_prefix=1):
        """

        :param app:
        :param x_for:
        :param x_proto:
        :param x_host:
        :param x_port:
        :param x_prefix:
        """
        super().__init__(app, x_for, x_proto, x_host, x_port, x_prefix)


class HTTPMethodOverride(object):
    """
    Implements the hidden HTTP method technique.
    Not all web browsers or reverse proxy supports every HTTP method.
    Client can use 'X-HTTP-Method-Override' header or '_method_override' in querystring.
    Only POST method can be overridden because with GET requests
    could result unexpected behavior due to caching.
    """
    def __init__(self, app):
        """

        :param app:
        """
        self.app = app

    def __call__(self, environ, start_response):
        """

        :param environ:
        :param start_response:
        :return:
        """
        method = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', None)

        if '_method_override' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('_method_override')

        if environ['REQUEST_METHOD'] == 'POST' and method:
            environ['REQUEST_METHOD'] = method.upper()

        return self.app(environ, start_response)
