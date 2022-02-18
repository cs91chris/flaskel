from unittest.mock import MagicMock

from vbcore.tester.mixins import Asserter

from flaskel.ext.default import client_redis


def test_init_app(flaskel_app):
    app = flaskel_app
    client_redis.init_app(app, redis_class=MagicMock())

    Asserter.assert_equals(app.extensions["redis"], client_redis)
    Asserter.assert_equals(app.config.REDIS_URL, "redis://localhost:6379/0")
    Asserter.assert_equals(
        app.config.REDIS_OPTS,
        {
            "decode_responses": True,
            "socket_connect_timeout": 1000,
        },
    )
