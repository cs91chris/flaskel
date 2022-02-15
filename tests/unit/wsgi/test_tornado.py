from unittest.mock import patch, MagicMock

from flaskel import Flaskel
from flaskel.wsgi.wsgi_tornado import WSGITornado


@patch("flaskel.wsgi.wsgi_tornado.IOLoop")
def test_run(mock_ioloop):
    _ = mock_ioloop
    app = Flaskel(__name__)
    options = {"bind": "0.0.0.0:8080"}

    server = WSGITornado(app=app, options=options)
    server.http_server.listen = MagicMock()
    server.run()
    server.http_server.listen.assert_called_once_with(address="0.0.0.0", port=8080)
