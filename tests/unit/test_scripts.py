import os
from unittest.mock import patch

from click.testing import CliRunner
from vbcore.tester.mixins import Asserter

from flaskel.scripts.cli import cli
from flaskel.scripts.init_app import init_app


@patch("flaskel.scripts.cli.init_app")
def test_init_app_entrypoint(mock_init_app):
    _ = mock_init_app

    runner = CliRunner()
    result = runner.invoke(cli, ["init", "testapp"])

    Asserter.assert_none(result.exception, error=result.output)
    Asserter.assert_equals(result.exit_code, 0)


def test_init_app(tmpdir):
    os.chdir(tmpdir.strpath)
    init_app("testapp")
