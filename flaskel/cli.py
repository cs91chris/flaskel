import os
import shutil
import sys
from pathlib import Path

import click

from flaskel.ext.sqlalchemy import db_to_schema, model_to_uml
from flaskel.tester import cli as cli_tester

INIT_CONTENT = """
# generated via cli
from .version import *
"""


@click.group()
def cli():
    """

    """
    pass


@cli.command(name='init')
@click.argument('name')
def init(name):
    """Create skeleton for new application"""
    import flaskel

    package_path = flaskel.__path__[0]
    source = os.path.join(package_path, 'skeleton')
    destination = name

    try:
        shutil.copytree(source, destination)

        init_file = Path(os.path.join(destination, '__init__.py'))
        init_file.write_text(INIT_CONTENT)

        if not os.path.isfile('setup.py'):
            shutil.move(os.path.join(destination, 'setup.py'), '.')

            setup_file = Path('setup.py')
            text = setup_file.read_text()
            text = text.replace('{skeleton}', name)
            setup_file.write_text(text)
        else:
            os.remove(os.path.join(destination, 'setup.py'))

        cli_file = Path(os.path.join(destination, 'cli.py'))
        text = cli_file.read_text()
        text = text.replace('from .ext', 'from {}.ext'.format(name))
        text = text.replace('from .blueprint', 'from {}.blueprint'.format(name))
        cli_file.write_text(text)
    except OSError as e:
        print('Unable to create new app. Error: %s' % str(e), file=sys.stderr)


@cli.command(name='tests')
def run_tests():
    """Run test suite from package tests in current directory"""
    cli_tester.main()


@cli.command(name='schema')
@click.option('-m', '--from-models', help='module of sqlalchemy models')
@click.option('-d', '--from-database', help='database url connection')
@click.option('-f', '--file', required=True, help='output png filename')
def dump_schema(from_models, from_database, file):
    """Create png schema of database"""
    if from_models:
        graph = model_to_uml(from_models)
    elif from_database:
        graph = db_to_schema(from_database)
    else:
        raise click.UsageError("One of -m or -d are required")

    graph.write_png(file)


if __name__ == '__main__':
    cli()
