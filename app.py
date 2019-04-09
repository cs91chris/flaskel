from flaskel import bootstrap
from blueprints import BLUEPRINTS
from flaskel.patch import DispatchError
from flaskel.patch import ReverseProxied
from flaskel.patch import force_https


def create_app():
    _app = bootstrap(bp=BLUEPRINTS)
    DispatchError.by_subdomain(_app)
    _app.wsgi_app = ReverseProxied(_app.wsgi_app)

    if not _app.config.get('DEBUG'):
        _app = force_https(_app)

    return _app


app = create_app()


if __name__ == '__main__':
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config['DEBUG']
    )
