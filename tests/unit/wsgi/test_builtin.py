from unittest.mock import MagicMock

import pytest
from vbcore.datastruct import ObjectDict

from flaskel import Flaskel
from flaskel.wsgi import WSGIBuiltin


# TODO: check why DEBUG is always True pylint: disable=fixme
@pytest.mark.parametrize(
    "options, params",
    [
        (
            {"bind": "0.0.0.0:8000"},
            ObjectDict(host="0.0.0.0", port=8000, debug=True),
        ),
        (
            {},
            ObjectDict(host="127.0.0.1", port=5000, debug=True),
        ),
        (
            {"bind": "localhost"},
            ObjectDict(host="localhost", port=5000, debug=True),
        ),
        (
            {"bind": ":8080"},
            ObjectDict(host="127.0.0.1", port=8080, debug=True),
        ),
    ],
)
def test_run(options, params):
    app = Flaskel(__name__)
    app.run = MagicMock()
    server = WSGIBuiltin(app=app, options=options)
    server.run()

    app.run.assert_called_once_with(**params)
