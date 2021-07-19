from blueprints import BLUEPRINTS, VIEWS
from ext import EXTENSIONS
from flaskel import AppBuilder, middlewares as middle, Server

APP_CONFIG = dict(
    static_folder=None,  # because static is inside web blueprint
    blueprints=BLUEPRINTS,
    extensions=EXTENSIONS,
    views=VIEWS,
    middlewares=(
        middle.RequestID,
        middle.HTTPMethodOverride,
        middle.ReverseProxied,
    ),
)

factory = AppBuilder(**APP_CONFIG)


def create_app(conf=None):
    """
    useful for external wsgi server

    :param conf:
    :return:
    """
    return factory.get_or_create(conf)


def cli():
    Server(factory).run_from_cli()


if __name__ == "__main__":
    cli()
