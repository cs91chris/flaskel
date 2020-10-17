from blueprints import BLUEPRINTS
from ext import EXTENSIONS
from flaskel import AppFactory, BASE_EXTENSIONS, Server

factory = AppFactory(
    blueprints=BLUEPRINTS,
    extensions={**BASE_EXTENSIONS, **EXTENSIONS}
)


def create_app(conf=None):
    """
i:qa
    useful for external wsgi server
uuuuu
    :param conf:
    :return:
    """
    return factory.get_or_create(conf)


if __name__ == '__main__':
    Server(factory).run_from_cli()
