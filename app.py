from flaskel import bootstrap
from flaskel.patch import ForceHttps
from flaskel.patch import ReverseProxied
from flaskel.patch import HTTPMethodOverride

from flask_errors_handler import SubdomainDispatcher


def create_app(**kwargs):
    """

    :return:
    """
    _app = bootstrap(**kwargs)

    if not _app.config.get('DEBUG'):
        _app.wsgi_app = ForceHttps(_app.wsgi_app)

    _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    error = _app.extensions['errors_handler']
    error.register_dispatcher(SubdomainDispatcher)
    return _app


app = create_app()


if __name__ == '__main__':
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config['DEBUG']
    )
