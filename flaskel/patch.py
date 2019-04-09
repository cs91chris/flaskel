from flask import request
from flask import make_response


def force_https(app):
    """

    :param app:
    :return:
    """
    def wrapper(environ, start_response):
        """

        :param environ:
        :param start_response:
        :return:
        """
        environ['wsgi.url_scheme'] = 'https'
        return app(environ, start_response)
    return wrapper


class DispatchError(object):
    @staticmethod
    def dispatch(app, dispatcher):
        """

        :param app:
        :param dispatcher:
        """
        @app.errorhandler(404)
        def handle_404(e):
            return dispatcher(e, 404, 'Not Found')

        @app.errorhandler(405)
        def handle_405(e):
            return dispatcher(e, 405, 'Method Not Allowed')

    @staticmethod
    def by_subdomain(app):
        """

        :param app:
        :return:
        """
        def dispatcher(e, code, mess):
            """

            :param e:
            :param code:
            :param mess:
            :return:
            """
            len_domain = len(app.config['SERVER_NAME'])
            subdomain = request.host[:-len_domain].rstrip('.') or None

            for bp_name, bp in app.blueprints.items():
                if subdomain == bp.subdomain:
                    handler = app.error_handler_spec.get(bp_name, {}).get(code)
                    for k, v in (handler or {}).items():
                        return v(e)

            return make_response(mess, code)
        DispatchError.dispatch(app, dispatcher)

    @staticmethod
    def by_url_prefix(app):
        """

        :param app:
        :return:
        """
        def dispatcher(e, code, mess):
            """

            :param e:
            :param code:
            :param mess:
            :return:
            """
            for bp_name, bp in app.blueprints.items():
                if request.path.startswith(bp.url_prefix or '/'):
                    handler = app.error_handler_spec.get(bp_name, {}).get(code)
                    for k, v in (handler or {}).items():
                        return v(e)

            return make_response(mess, code)
        DispatchError.dispatch(app, dispatcher)


class ReverseProxied(object):
    """
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.
    In nginx:

    location /myprefix {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
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
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', None)
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        return self.app(environ, start_response)
