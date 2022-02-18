from functools import partial

import flask
from vbcore.http.useragent import UserAgent as UserAgentParser

from flaskel.flaskel import request


class UserAgent:
    def __init__(self, app=None, **kwargs):
        self._parser = None

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, parser_class=UserAgentParser):
        self._parser = parser_class
        app.config.setdefault("USER_AGENT_AUTO_PARSE", False)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["useragent"] = self

        app.before_request_funcs.setdefault(None, []).append(
            partial(self.before_request_hook, app)
        )

    def before_request_hook(self, app):
        flask.g.user_agent = self._parser  # pylint: disable=assigning-non-slot
        if app.config.USER_AGENT_AUTO_PARSE:
            ua_str = request.user_agent.string
            # pylint: disable=assigning-non-slot
            flask.g.user_agent = self._parser.parse(ua_str)
