from unittest.mock import patch

from flaskel import Flaskel
from flaskel.wsgi.wsgi_twisted import WSGITwisted


@patch("flaskel.wsgi.wsgi_twisted.reactor")
def test_run(mock_reactor):
    app = Flaskel(__name__)
    options = {"bind": "0.0.0.0:8080"}

    server = WSGITwisted(app=app, options=options)
    server.run()

    mock_reactor.listenTCP.assert_called_once_with(
        8080, server.site, interface="0.0.0.0"
    )
