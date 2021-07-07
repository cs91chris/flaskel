import os
import shutil
import sys
from pathlib import Path

import click

from flaskel.ext.sqlalchemy.schema import db_to_schema, model_to_uml
from flaskel.tester import cli as cli_tester

INIT_CONTENT = "from .version import *"


@click.group()
def cli():
    pass


@cli.command(name='init')
@click.argument('name')
def init(name):
    """Create skeleton for new application"""
    from flaskel import scripts as flaskel_scripts

    package_path = flaskel_scripts.__path__[0]
    source = os.path.join(package_path, 'skeleton')

    try:
        shutil.copytree(source, '.', dirs_exist_ok=True)
        shutil.move('skel', name)

        init_file = Path(os.path.join(name, '__init__.py'))
        init_file.write_text(INIT_CONTENT)

        setup_file = Path('setup.py')
        text = setup_file.read_text()
        text = text.replace('{skeleton}', name)
        setup_file.write_text(text)

        def replace_package_import(file):
            cli_file = Path(file)
            t = cli_file.read_text()
            t = t.replace('from ext', f"from {name}.ext")
            t = t.replace('from blueprint', f"from {name}.blueprint")
            cli_file.write_text(t)

        replace_package_import(os.path.join('tests', '__init__.py'))
        replace_package_import(os.path.join(name, 'scripts', 'cli.py'))
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
