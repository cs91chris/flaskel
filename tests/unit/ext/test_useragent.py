import flask
from vbcore.tester.mixins import Asserter

from flaskel.ext.default import useragent


def test_init_app(flaskel_app):
    useragent.init_app(flaskel_app)
    Asserter.assert_equals(flaskel_app.extensions["useragent"], useragent)
    Asserter.assert_false(flaskel_app.config.USER_AGENT_AUTO_PARSE)


def test_before_request(flaskel_app):
    app = flaskel_app
    app.config["USER_AGENT_AUTO_PARSE"] = True

    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/44.0.2403.157 Safari/537.36"
    )

    with app.test_request_context(headers={"User-Agent": ua}):
        useragent.init_app(app)
        useragent.before_request_hook(app)
        Asserter.assert_equals(flask.g.user_agent.raw, ua)
