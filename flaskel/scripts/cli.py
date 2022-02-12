import click

from flaskel.scripts.init_app import init_app

cli = click.Group()


@cli.command(name="init")
@click.argument("name")
def init(name):
    """Create skeleton for new application"""
    init_app(name)


if __name__ == "__main__":
    cli()
