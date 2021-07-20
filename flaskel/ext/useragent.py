import flask

from flaskel.http.useragent import UserAgent as UserAgentParser


class UserAgent:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        :param kwargs:
        """
        self._parser = None

        if app is not None:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(self, app, parser_class=UserAgentParser):
        """

        :param app:
        :param parser_class:
        """
        self._parser = parser_class
        app.config.setdefault("USER_AGENT_AUTO_PARSE", False)

        if not hasattr(app, "extensions"):
            app.extensions = {}  # pragma: no cover
        app.extensions["useragent"] = self

        @app.before_request
        def before_request():
            # pylint: disable=E0237
            flask.g.user_agent = self._parser(flask.request.user_agent.string)
            if app.config["USER_AGENT_AUTO_PARSE"]:
                flask.g.user_agent.parse()


useragent = UserAgent()
