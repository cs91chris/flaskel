import argon2 as _argon2
from vbcore.crypto.argon import Argon2 as HasherArgon2


class Argon2:
    def __init__(self, app=None, **kwargs):
        self._argon = None

        if app is not None:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(self, app, argon_class=HasherArgon2):
        app.config.setdefault("ARGON2_ENCODING", "utf-8")
        app.config.setdefault("ARGON2_TIME_COST", _argon2.DEFAULT_TIME_COST)
        app.config.setdefault("ARGON2_HASH_LEN", _argon2.DEFAULT_HASH_LENGTH)
        app.config.setdefault("ARGON2_MEMORY_COST", _argon2.DEFAULT_MEMORY_COST)
        app.config.setdefault("ARGON2_PARALLELISM", _argon2.DEFAULT_PARALLELISM)
        app.config.setdefault("ARGON2_SALT_LEN", _argon2.DEFAULT_RANDOM_SALT_LENGTH)

        self._argon = argon_class(**app.config.get_namespace("ARGON2_"))
        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["argon2"] = self

    def __getattr__(self, item):
        return getattr(self._argon, item)
