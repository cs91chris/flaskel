import sys

import argon2
import click

from flaskel.ext.sqlalchemy.schema import db_to_schema, dump_model_ddl, DIALECTS
from flaskel.ext.sqlalchemy.schema import model_to_uml
from flaskel.scripts.init_app import init_app
from flaskel.tester import cli as cli_tester

cli = click.Group()
main_password = click.Group(name="password", help="tools for password")
main_database = click.Group(name="database", help="tools for database")


@cli.command(name="init")
@click.argument("name")
def init(name):
    """Create skeleton for new application"""
    init_app(name)


@cli.command(name="tests")
def run_tests():
    """Run test suite from package tests in current directory"""
    cli_tester.main()


@main_password.command(name="hash")
@click.argument("password")
def hash_password(password):
    """Print the argon2 hash of a given password"""
    print(argon2.PasswordHasher().hash(password))


@main_database.command(name="schema")
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


@main_database.command(name="ddl")
@click.option("--dialect", default="sqlite", type=click.Choice(DIALECTS))
@click.option("-m", "--metadata", help="metadata module", required=True)
def dump_ddl(dialect, metadata):
    """Dumps the create table statements for a given metadata"""
    dump_model_ddl(dialect, metadata)


cli.add_command(main_password)
cli.add_command(main_database)

if __name__ == "__main__":
    cli()
