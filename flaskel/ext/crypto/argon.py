import typing as t

import argon2
from vbcore.crypto.argon import Argon2 as HasherArgon2


class Argon2:
    CONFIG_PREFIX = "ARGON2_"
    PROFILES: t.Dict[str, argon2.Parameters] = {
        "low": argon2.profiles.RFC_9106_LOW_MEMORY,
        "high": argon2.profiles.RFC_9106_HIGH_MEMORY,
    }

    def __init__(self, app=None, **kwargs):
        self._argon = None

        if app is not None:
            self.init_app(app, **kwargs)

    @classmethod
    def set_default_config(cls, app):
        app.config.setdefault(f"{cls.CONFIG_PREFIX}PROFILE", "low")
        app.config.setdefault(f"{cls.CONFIG_PREFIX}ENCODING", "utf-8")

        argon_profile = app.config.pop(f"{cls.CONFIG_PREFIX}PROFILE", None)
        if argon_profile not in cls.PROFILES:
            profiles = tuple(cls.PROFILES.values())
            raise ValueError(f"profile not allowed, choose one of: {profiles}")

        params = cls.PROFILES[argon_profile]
        app.config.setdefault(f"{cls.CONFIG_PREFIX}TIME_COST", params.time_cost)
        app.config.setdefault(f"{cls.CONFIG_PREFIX}HASH_LEN", params.hash_len)
        app.config.setdefault(f"{cls.CONFIG_PREFIX}MEMORY_COST", params.memory_cost)
        app.config.setdefault(f"{cls.CONFIG_PREFIX}PARALLELISM", params.parallelism)
        app.config.setdefault(f"{cls.CONFIG_PREFIX}SALT_LEN", params.salt_len)

    def init_app(self, app, argon_class: t.Type[HasherArgon2] = HasherArgon2):
        self.set_default_config(app)
        self._argon = argon_class(**app.config.get_namespace(self.CONFIG_PREFIX))
        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["argon2"] = self

    def __getattr__(self, item):
        return getattr(self._argon, item)
