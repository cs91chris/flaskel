import click

from flaskel import AppFactory, BASE_EXTENSIONS, serve_forever
from flaskel.wsgi import DEFAULT_WSGI

from blueprints import BLUEPRINTS
from ext import EXTENSIONS


wsgi_types = click.Choice(DEFAULT_WSGI, case_sensitive=False)


def create_app():
    """

    :return: app instance
    """
    return AppFactory().getOrCreate(
        blueprints=BLUEPRINTS,
        extensions={**BASE_EXTENSIONS, **EXTENSIONS}
    )


@click.command()
@click.option('-d', '--debug', is_flag=True, flag_value=True, default=False, help='enable debug mode')
@click.option('-c', '--config', default=None, help='app yaml configuration file')
@click.option('-l', '--log-config', default=None, help='alternative log yaml configuration file')
@click.option('-w', '--wsgi-server', default=None, type=wsgi_types, help='name of wsgi server to use')
@click.option('-b', '--bind', default='127.0.0.1:5000', help='address to bind', show_default=True)
def cli(config, log_config, bind, debug, wsgi_server):
    """

    :param config: app and wsgi configuration file
    :param log_config: log configuration file
    :param bind: address to bind
    :param debug: enable debug mode
    :param wsgi_server: wsgi server chosen
    :return: never returns
    """
    serve_forever(
        app=create_app(),
        config=config,
        log_config=log_config,
        bind=bind,
        debug=debug,
        wsgi_server=wsgi_server
    )


if __name__ == '__main__':
    cli()
