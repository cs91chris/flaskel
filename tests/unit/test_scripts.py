import os
from unittest.mock import patch

from click.testing import CliRunner
from vbcore.tester.mixins import Asserter

from flaskel.scripts.cli import cli
from flaskel.scripts.init_app import DEVOPS_DIR, init_app, SERVICES_DIR


@patch("flaskel.scripts.cli.init_app")
def test_init_app_entrypoint(mock_init_app):
    _ = mock_init_app

    runner = CliRunner()
    result = runner.invoke(cli, ["init", "testapp"])

    Asserter.assert_none(result.exception, error=result.output)
    Asserter.assert_equals(result.exit_code, 0)


def test_init_app(tmpdir):
    home = tmpdir.strpath
    new_app_name = "testapp"
    new_package = os.path.join(home, new_app_name)
    devops_base_dir = os.path.join(DEVOPS_DIR, "base")

    os.chdir(home)
    init_app(new_app_name)

    for base_dir, directory in (
        (home, new_app_name),
        (home, "devops"),
        (home, ".git-hooks"),
        (home, "requirements"),
        (home, "tests"),
        (home, "resources"),
        (new_package, "ext"),
        (new_package, "forms"),
        (new_package, "models"),
        (new_package, "scripts"),
        (new_package, "tasks"),
        (new_package, "views"),
        (devops_base_dir, "config"),
        (devops_base_dir, "scripts"),
        (SERVICES_DIR, new_app_name),
    ):
        Asserter.assert_true(os.path.isdir(os.path.join(base_dir, directory)))

    for base_dir, file in (
        (home, ".bumpversion.cfg"),
        (home, ".coveragerc"),
        (home, ".flake8"),
        (home, "Makefile"),
        (home, "MANIFEST.in"),
        (home, "mypy.ini"),
        (home, ".pylintrc"),
        (home, "pytest.ini"),
        (home, "setup.py"),
        (home, "tox.ini"),
        (new_package, "__init__.py"),
        (new_package, "version.py"),
        (DEVOPS_DIR, "build.sh"),
        (DEVOPS_DIR, "Dockerfile"),
        (DEVOPS_DIR, "docker-compose.yaml"),
        (os.path.join(devops_base_dir, "scripts"), "entrypoint"),
    ):
        Asserter.assert_true(os.path.isfile(os.path.join(base_dir, file)))
