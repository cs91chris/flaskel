from flask_response_builder.builders.encoders import JsonEncoder

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

try:
    from rejson import Client, Path
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    Client = Path = object


class JSONRedisClient(Client):
    def __init__(self, encoder=None, *args, **kwargs):
        super().__init__(encoder or JsonEncoder(), *args, **kwargs)

    @staticmethod
    def json_path(path=None):
        return Path(path) if path else Path.rootPath()

    def json_set(self, key, data, path=None):
        return self.jsonset(key, self.json_path(path), data)

    def json_get(self, key, path=None):
        return self.jsonget(key, self.json_path(path))

    def json_array_add(self, key, data, path=None, **kwargs):
        path = self.json_path(path)
        pipe = self.pipeline()
        pipe.jsonset(key, path, [], nx=True)
        pipe.jsonarrappend(key, path, data)
        return pipe.execute()[1]


class FlaskRedis:
    def __init__(self, app=None, client=None, **kwargs):
        """

        :param app:
        :param client:
        :param kwargs:
        """
        self._client = client

        if app is not None:
            self.init_app(app, **kwargs)  # pragma: no cover

    @property
    def client(self):
        return self._client  # pragma: no cover

    def init_app(self, app, redis_class=None, **kwargs):
        """

        :param app:
        :param redis_class:
        """
        assert redis is not None, "redis must be installed"
        if redis_class is None:
            if Client is object:
                redis_class = redis.StrictRedis
            else:
                redis_class = JSONRedisClient

        app.config.setdefault("REDIS_URL", "redis://localhost:6379/0")
        app.config.setdefault("REDIS_OPTS", **kwargs)

        if not self._client:
            self._client = redis_class.from_url(
                app.config["REDIS_URL"],
                **app.config["REDIS_OPTS"]
            )

        if not hasattr(app, "extensions"):
            app.extensions = {}  # pragma: no cover
        app.extensions['redis'] = self

    def __getattr__(self, name):
        return getattr(self._client, name)


client_redis = FlaskRedis()
