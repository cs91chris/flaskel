from vbcore.tester.asserter import Asserter

from flaskel import Flaskel
from flaskel.wsgi.wsgi_gevent import WSGIGevent


def test_run():
    app = Flaskel(__name__)
    options = {"bind": "0.0.0.0:8080", "backlog": 1000}
    server = WSGIGevent(app=app, options=options)

    Asserter.assert_equals(server.backlog, 1000)
    Asserter.assert_equals(server.server_host, "0.0.0.0")
    Asserter.assert_equals(server.server_port, 8080)
