from werkzeug.urls import url_decode


class ForceHttps(object):
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


class ReverseProxied(object):
    """
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally. In nginx:

    location /prefix {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /prefix;
    }

    :param app: the WSGI application
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
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']

            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', None)
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        return self._app(environ, start_response)


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
        self._app = app

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

        return self._app(environ, start_response)
