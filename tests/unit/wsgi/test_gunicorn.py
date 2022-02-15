from vbcore.tester.mixins import Asserter

from flaskel import Flaskel
from flaskel.wsgi.wsgi_gunicorn import WSGIGunicorn


def test_load_config():
    app = Flaskel(__name__)
    options = {"bind": "0.0.0.0:8080"}

    server = WSGIGunicorn(app=app, options=options)
    server.load_config()

    config = server.cfg.settings
    Asserter.assert_equals(config["preload_app"].value, True)
    Asserter.assert_equals(config["post_fork"].value, server.post_fork)
    Asserter.assert_equals(config["pre_fork"].value, server.pre_fork)
    Asserter.assert_equals(config["pre_exec"].value, server.pre_exec)
    Asserter.assert_equals(config["when_ready"].value, server.when_ready)
    Asserter.assert_equals(config["worker_abort"].value, server.worker_abort)
    Asserter.assert_equals(config["worker_int"].value, server.worker_int)
    Asserter.assert_equals(config["bind"].value, ["0.0.0.0:8080"])
    Asserter.assert_equals(config["pidfile"].value, ".gunicorn.pid")
    Asserter.assert_equals(config["proc_name"].value, None)
    Asserter.assert_equals(config["timeout"].value, 30)
    Asserter.assert_equals(config["backlog"].value, 2048)
    Asserter.assert_equals(config["keepalive"].value, 3)
    Asserter.assert_equals(config["errorlog"].value, "-")
    Asserter.assert_equals(config["accesslog"].value, "-")
    Asserter.assert_equals(config["loglevel"].value, "info")
    Asserter.assert_greater(config["workers"].value, 2)
    Asserter.assert_equals(config["threads"].value, 1)
    Asserter.assert_equals(config["worker_connections"].value, 1000)
    Asserter.assert_equals(config["worker_class"].value, "sync")
    Asserter.assert_equals(config["access_log_format"].value, server.default_log_format)
