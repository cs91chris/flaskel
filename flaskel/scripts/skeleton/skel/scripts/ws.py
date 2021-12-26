try:
    from gevent import monkey

    monkey.patch_all()
except ImportError:
    try:
        from eventlet import monkey_patch

        monkey_patch()
    except ImportError:
        pass

from typing import Dict

import click

from flaskel import AppBuilder, middlewares as middle
from flaskel.ext.websocket import socketio

EXTENSIONS: Dict[str, Dict] = {}

APP_CONFIG = dict(
    static_folder=None,
    extensions=EXTENSIONS,
    middlewares=(
        middle.RequestID,
        middle.ReverseProxied,
    ),
)


def get_app():
    return AppBuilder(**APP_CONFIG).get_or_create()


@click.command()
@click.option("-p", "--port", default=5000, type=int)
@click.option("-H", "--bind", default="127.0.0.1")
def cli(port, bind):
    app = get_app()
    socketio.run(app, host=bind, port=port, debug=app.debug, log_output=app.debug)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
