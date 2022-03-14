from redis import StrictRedis
from vbcore.date_helper import Seconds


class FlaskRedis:
    def __init__(self, app=None, client=None, **kwargs):
        self._client = client

        if app is not None:
            self.init_app(app, **kwargs)

    @property
    def client(self):
        return self._client

    def init_app(self, app, redis_class=StrictRedis, **kwargs):
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
        return getattr(self.client, name)
