from blueprints import BLUEPRINTS
from ext import EXTENSIONS
from flaskel import AppBuilder, BASE_EXTENSIONS, Server

factory = AppBuilder(
    blueprints=BLUEPRINTS,
    extensions={**BASE_EXTENSIONS, **EXTENSIONS}
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
