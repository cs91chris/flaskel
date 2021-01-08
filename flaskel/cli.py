import os
import shutil
import sys
from pathlib import Path

import click

from .ext.sqlalchemy import db_to_schema, model_to_uml
from .tester import cli as cli_tester

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

        if not os.path.isdir('config'):
            shutil.move(os.path.join(destination, 'config'), '.')
        else:
            os.remove(os.path.join(destination, 'config'))

        if not os.path.isfile('Dockerfile'):
            shutil.move(os.path.join(destination, 'Dockerfile'), '.')
        else:
            os.remove(os.path.join(destination, 'Dockerfile'))

        if not os.path.isdir('tests'):
            shutil.move(os.path.join(destination, 'tests'), '.')
            cli_file = Path(os.path.join('tests', '__init__.py'))
            text = cli_file.read_text()
            text = text.replace('from ext', f"from {name}.ext")
            text = text.replace('from blueprint', f"from {name}.blueprint")
            cli_file.write_text(text)
        else:
            os.remove(os.path.join(destination, 'tests'))

        cli_file = Path(os.path.join(destination, 'cli.py'))
        text = cli_file.read_text()
        text = text.replace('from ext', f"from {name}.ext")
        text = text.replace('from blueprint', f"from {name}.blueprint")
        cli_file.write_text(text)
    except OSError as e:
        print(f"Unable to create new app. Error: {e}", file=sys.stderr)


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
