from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.urls import url_decode

from .utils import uuid
from .utils.datastruct import ObjectDict


class BaseMiddleware:
    # noinspection PyUnresolvedReferences
    def get_config(self):
        try:
            # flask_app is added by flaskel factory as a workaround
            if isinstance(self.flask_app.config, ObjectDict):
                return self.flask_app.config
            return ObjectDict.normalize(self.flask_app.config)  # pragma: no cover
        except AttributeError:  # pragma: no cover
            return ObjectDict()


class ForceHttps(BaseMiddleware):
    """
    NOTE: use this only if you can not touch reverse proxy configuration
    use ReverseProxied instead
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
        conf = self.get_config()
        url_scheme = conf.PREFERRED_URL_SCHEME or "https"
        environ["wsgi.url_scheme"] = url_scheme
        return self.app(environ, start_response)


class ReverseProxied(ProxyFix, BaseMiddleware):
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
            proxy_set_header X-Forwarded-Proto $proto;
            proxy_set_header X-Forwarded-Port 5000;
            proxy_set_header X-Forwarded-Prefix /prefix;
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


class HTTPMethodOverride(BaseMiddleware):
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
        conf = self.get_config()
        methods = conf.OVERRIDE_METHODS or ("POST",)
        method = environ.get("HTTP_X_HTTP_METHOD_OVERRIDE", None)

        if "_method_override" in environ.get("QUERY_STRING", ""):
            args = url_decode(environ["QUERY_STRING"])
            method = args.get("_method_override")

        if method and environ["REQUEST_METHOD"] in methods:
            environ["REQUEST_METHOD"] = method.upper()

        return self.app(environ, start_response)


class RequestID(BaseMiddleware):
    """
    From: https://github.com/antarctica/flask-request-id-header

    Flask middleware to ensure all requests have a Request ID header present.
    Request IDs can be used when logging errors and allows users to trace requests through multiple
    layers such as load balancers and reverse proxies. The request ID header value may consist of multiple
    IDs encoded according to RFC 2616 [1].

    This middleware ensures there is always at least one, unique, value, whilst respecting any pre-existing
    values set by an upstream component or the client. If there isn't a pre-existing value, a single, unique,
    ID is generated.
    If there is a pre-existing value, it is split into multiple values as per RFC 2616 and each value checked
    for uniqueness. If no values are unique an additional, unique, value is added.

    A value is considered unique if it:
    1. is a valid UUID (version 4)
    2. or, the value is known to be from a component that assigns unique IDs, identified by a common prefix
       set in the 'REQUEST_ID_PREFIX' Flask config value or `request_id_prefix` class member value.

    To use the Request ID in the current application: `request.environ.get("HTTP_X_REQUEST_ID")`
    For use elsewhere, the Request ID header is included in the response back to the client.
    [1] http://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.2
    """

    # the http header name, overridden via flask app config
    header_name = "X-Request-ID"

    # the request id value prefix used to trust uniqueness
    request_id_prefix = None

    def __init__(self, app):
        """

        :param app: Flask application
        """
        self.app = app

    def __call__(self, environ, start_response):
        """

        :param environ:
        :param start_response:
        :return:
        """
        conf = self.get_config()
        header_name = conf.REQUEST_ID_HEADER or self.header_name
        flask_header_name = f"HTTP_{header_name.upper().replace('-', '_')}"
        request_id_header = self._compute_request_id_header(
            environ.get(flask_header_name)
        )
        environ[flask_header_name] = request_id_header

        def new_start_response(status, headers, exc_info=None):
            headers.append((header_name, request_id_header))
            return start_response(status, headers, exc_info)

        return self.app(environ, new_start_response)

    def _compute_request_id_header(self, header_value):
        """
        Ensures request ID header has at least one, unique, value

        :param header_value: Existing request ID HTTP header value
        :return: Computed Request ID HTTP header
        """
        if header_value is None:
            return uuid.get_uuid()

        for request_id in header_value.split(","):
            if self._is_unique(request_id):
                return header_value

        # Append an unique header value
        return f"{header_value},{uuid.get_uuid()}"

    def _is_unique(self, request_id):
        """
        Checks whether a Request ID is unique

        :param request_id: A request ID
        :return: Whether the Request ID is unique or not
        """
        conf = self.get_config()
        request_id_prefix = conf.REQUEST_ID_PREFIX or self.request_id_prefix
        if request_id_prefix is not None and request_id.startswith(request_id_prefix):
            return True  # pragma: no cover

        try:
            uuid.check_uuid(request_id, exc=True)
        except ValueError:
            return False
        else:
            return True
