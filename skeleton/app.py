from flask_response_builder import encoders
from flask_errors_handler import SubdomainDispatcher

from blueprints import BLUEPRINTS
from flaskel.ext import EXTENSIONS
from flaskel import bootstrap
from flaskel.patch import ForceHttps, ReverseProxied, HTTPMethodOverride


def create_app(**kwargs):
    """

    :return:
    """
    _app = bootstrap(blueprints=BLUEPRINTS, extensions=EXTENSIONS, **kwargs)

    if not _app.config.get('DEBUG'):
        _app.wsgi_app = ForceHttps(_app.wsgi_app)

    _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    _app.json_encoder = encoders.JsonEncoder
    error = _app.extensions['errors_handler']
    error.register_dispatcher(SubdomainDispatcher)
    return _app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config['DEBUG']
    )