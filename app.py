from flaskel import bootstrap
from blueprints import BLUEPRINTS


def create_app():
    return bootstrap(bp=BLUEPRINTS)


app = create_app()


if __name__ == '__main__':
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config['DEBUG']
    )

