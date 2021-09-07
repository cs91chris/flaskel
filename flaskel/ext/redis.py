from flask_response_builder.builders.encoders import JsonEncoder

from flaskel.utils import Seconds

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore

try:
    from rejson import Client, Path
    from rejson.client import Pipeline as BasePipeline
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    Client = Path = BasePipeline = object  # type: ignore


class JSONRedisClient(Client):
    def __init__(self, *args, encoder=None, **kwargs):
        super().__init__(encoder or JsonEncoder(), *args, **kwargs)

    @staticmethod
    def json_path(path: str = None):
        return Path(path) if path else Path.rootPath()

    def json_set(self, key: str, data, path: str = None):
        return self.jsonset(key, self.json_path(path), data)

    def json_get(self, key: str, path: str = None):
        return self.jsonget(key, self.json_path(path))

    def json_array_add(self, key: str, data, path: str = None, **__):
        path = self.json_path(path)
        pipe = self.pipeline()
        pipe.jsonset(key, path, [], nx=True)
        pipe.jsonarrappend(key, path, data)
        return pipe.execute()[1]

    def pipeline(self, transaction: bool = True, shard_hint: bool = None):
        pipe = Pipeline(
            connection_pool=self.connection_pool,
            response_callbacks=self.response_callbacks,
            transaction=transaction,
            shard_hint=shard_hint,
        )
        return pipe


class Pipeline(BasePipeline, JSONRedisClient):
    """Pipeline for JSONRedisClient"""


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

        app.config.setdefault("REDIS_OPTS", {})
        app.config["REDIS_OPTS"].setdefault("decode_responses", True)
        app.config["REDIS_OPTS"].setdefault("socket_connect_timeout", Seconds.millis)
        app.config["REDIS_OPTS"].update(**kwargs)

        if not self._client:
            self._client = redis_class.from_url(
                app.config["REDIS_URL"], **app.config["REDIS_OPTS"]
            )

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["redis"] = self

    def __getattr__(self, name):
        return getattr(self._client, name)


client_redis = FlaskRedis()
