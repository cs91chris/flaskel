from unittest.mock import patch

from flaskel import Flaskel
from flaskel.wsgi.wsgi_waitress import WSGIWaitress


@patch("flaskel.wsgi.wsgi_waitress.serve")
def test_run(mock_serve):
    app = Flaskel(__name__)
    options = {"bind": "0.0.0.0:8080", "threads": 4}
    server = WSGIWaitress(app=app, options=options)
    server.run()

    mock_serve.assert_called_once_with(
        app,
        host="0.0.0.0",
        port=8080,
        threads=4,
    )
