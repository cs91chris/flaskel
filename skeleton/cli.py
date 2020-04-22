from flaskel import serve_forever, default_app_factory

from blueprints import BLUEPRINTS
from flaskel.ext import EXTENSIONS


def cli():
    """

    """
    serve_forever(
        default_app_factory,
        blueprints=BLUEPRINTS,
        extensions=EXTENSIONS
    )


if __name__ == '__main__':
    cli()
