from blueprints import BLUEPRINTS
from ext import EXTENSIONS
from flaskel import AppBuilder, BASE_EXTENSIONS, middlewares as middle, Server

factory = AppBuilder(
    static_folder=None,  # because static is inside web blueprint
    blueprints=BLUEPRINTS,
    extensions={**BASE_EXTENSIONS, **EXTENSIONS},
    middlewares=(
        middle.RequestID,
        middle.HTTPMethodOverride,
        middle.ReverseProxied,
    )
)


def create_app(conf=None):
    """
    useful for external wsgi server

    :param conf:
    :return:
    """
    return factory.get_or_create(conf)


def cli():
    Server(factory).run_from_cli()


if __name__ == '__main__':
    cli()
