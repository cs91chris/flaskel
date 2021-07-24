import os
import shutil
import sys
from pathlib import Path

import click

from flaskel.ext.sqlalchemy.schema import db_to_schema
from flaskel.ext.sqlalchemy.schema import model_to_uml
from flaskel.tester import cli as cli_tester


@click.group()
def cli():
    pass


@cli.command(name="init")
@click.argument("name")
def init(name):
    """Create skeleton for new application"""
    from flaskel import scripts as flaskel_scripts  # pylint: disable=C0415

    try:
        source = os.path.join(flaskel_scripts.__path__[0], "skeleton")
        shutil.copytree(source, ".", dirs_exist_ok=True)
        shutil.move("skel", name)
    except OSError as e:
        print(f"Unable to create new app. Error: {e}", file=sys.stderr)
        sys.exit(1)

    def replace_in_file(file, *args):
        _f = Path(file)
        text = _f.read_text()
        for sd in args:
            text = text.replace(*sd)
        _f.write_text(text)

    init_file = Path(os.path.join(name, "__init__.py"))
    init_file.write_text("from .version import *\n")

    for f in (
        "setup.py",
        "Dockerfile",
        "Makefile",
        "pytest.ini",
        ".coveragerc",
        ".bumpversion.cfg",
    ):
        replace_in_file(f, ("{skeleton}", name))

    replace_in_file(
        os.path.join(name, "scripts", "cli.py"),
        ("from ext", f"from {name}.ext"),
        ("from blueprint", f"from {name}.blueprint"),
    )
    replace_in_file(
        os.path.join(name, "scripts", "gunicorn.py"),
        ("from . import config", f"from {name}.scripts import config"),
    )
    replace_in_file(
        os.path.join("tests", "__init__.py"),
        ("from scripts.cli", f"from {name}.scripts.cli"),
    )


@cli.command(name="tests")
def run_tests():
    """Run test suite from package tests in current directory"""
    cli_tester.main()


@cli.command(name="schema")
@click.option("-m", "--from-models", help="module of sqlalchemy models")
@click.option("-d", "--from-database", help="database url connection")
@click.option("-f", "--file", required=True, help="output png filename")
def dump_schema(from_models, from_database, file):
    """Create png schema of database"""
    if from_models:
        graph = model_to_uml(from_models)
    elif from_database:
        graph = db_to_schema(from_database)
    else:
        raise click.UsageError("One of -m or -d are required")

    try:
        graph.write_png(file)  # pylint: disable=E1101
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        print("try to install 'graphviz'", file=sys.stderr)


if __name__ == "__main__":
    cli()
