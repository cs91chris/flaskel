from flaskel import bootstrap
from flaskel.patch import force_https
from flaskel.patch import DispatchError
from flaskel.patch import ReverseProxied


def create_app():
    """

    :return:
    """
    _app = bootstrap()
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
