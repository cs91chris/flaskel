try:
    import redis
except ImportError:
    redis = None


class FlaskRedis:
    def __init__(self, app=None, client=None, **kwargs):
        """

        :param app:
        :param client:
        :param kwargs:
        """
        self._opts = kwargs
        self._client = client

        if app is not None:
            self.init_app(app)  # pragma: no cover

    @property
    def client(self):
        return self._client

    def init_app(self, app):
        """

        :param app:
        """
        assert redis is not None, "redis must be installed"

        app.config.setdefault("REDIS_URL", "redis://localhost:6379/0")
        app.config.setdefault("REDIS_OPTS", self._opts)

        if not self._client:
            # noinspection PyUnresolvedReferences
            self._client = redis.StrictRedis.from_url(
                app.config["REDIS_URL"], **app.config["REDIS_OPTS"]
            )

        if not hasattr(app, "extensions"):
            app.extensions = {}  # pragma: no cover
        app.extensions['redis'] = self

    def __getattr__(self, name):
        return getattr(self._client, name)


client_redis = FlaskRedis()
