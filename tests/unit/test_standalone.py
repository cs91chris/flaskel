import json
import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from vbcore.datastruct import ObjectDict
from vbcore.tester.mixins import Asserter

from flaskel import Server


@patch("flaskel.standalone.yaml")
def test_prepare_config(mock_yaml):
    flask_env = "development"
    bind_address = "127.0.0.1:5000"
    mock_yaml.load_yaml_file.side_effect = lambda _: ObjectDict(app={}, wsgi={})

    server = Server(app_factory=MagicMock(), wsgi_factory=MagicMock())
    config = server.prepare_config(
        debug=True,
        filename="config.yaml",
        log_config="log_config.yaml",
        bind=bind_address,
    )

    Asserter.assert_equals(
        config,
        {
            "app": {
                "FLASK_ENV": flask_env,
                "LOG_FILE_CONF": "log_config.yaml",
                "DEBUG": True,
            },
            "wsgi": {"bind": bind_address},
        },
    )
    Asserter.assert_equals(os.environ["FLASK_ENV"], flask_env)
    Asserter.assert_equals(os.environ["FLASK_DEBUG"], "1")


def test_run_from_cli(tmpdir):
    config_file = tmpdir.join("test_run_from_cli.yaml")
    config_data = {"app": {}, "wsgi": {}}
    config_file.write(json.dumps(config_data))

    runner = CliRunner()
    server = Server(app_factory=MagicMock(), wsgi_factory=MagicMock())

    result = runner.invoke(
        server.runner(),
        [
            # fmt: off
            "--debug",
            "--bind",        "127.0.0.1:5000",
            "--config",      config_file.strpath,
            "--log-config",  "log_config.yaml",
            "--wsgi-server", "gunicorn",
            "--app-config",  "SECRET_KEY=secret",
            "--wsgi-config", "WORKERS=4",
            # fmt: on
        ],
    )

    assert result.exception is None, result.output
    assert result.exit_code == 0
