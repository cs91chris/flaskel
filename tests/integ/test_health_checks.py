from unittest.mock import MagicMock

from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.asserter import Asserter

from flaskel.ext.default import Database
from flaskel.ext.healthcheck import HealthCheck
from flaskel.ext.healthcheck.checkers import (
    health_mongo,
    health_redis,
    health_services,
    health_sqlalchemy,
    health_system,
)
from flaskel.ext.mongo import FlaskMongoDB
from flaskel.ext.redis import FlaskRedis
from flaskel.tester.helpers import ApiTester
from flaskel.utils.schemas.default import SCHEMAS


def test_health_checks(testapp):
    database = Database()
    client_mongo = FlaskMongoDB()
    client_redis = FlaskRedis(client=MagicMock())

    app = testapp(
        config=ObjectDict(
            MONGO_URI="mongodb://localhost/test",
            MONGO_OPTS={"timeout": 1},
            HEALTH_SERVICES={
                "test-service-pass": {
                    "url": "https://httpbin.org/status/200",
                },
                "test-service-fail": {
                    "url": "https://httpbin.org/status/500",
                },
            },
        ),
        extensions={
            "database": (database,),
            "redis": (client_redis,),
            "mongo": (client_mongo,),
            "health_checks": (
                HealthCheck(),
                {
                    "checkers": (
                        (health_mongo, {"db": client_mongo}),
                        (health_redis, {"db": client_redis}),
                        (health_sqlalchemy, {"db": database}),
                        (health_services, {}),
                        (
                            health_system,
                            {
                                "config": ObjectDict(
                                    SYSTEM_FS_MOUNT_POINTS=("/",),
                                    SYSTEM_DUMP_ALL=True,
                                )
                            },
                        ),
                    )
                },
            ),
        },
    )

    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON_HEALTH)
    response = client.get(
        view=app.config.HEALTHCHECK_VIEW_NAME,
        status=httpcode.MULTI_STATUS,
        schema=SCHEMAS.HEALTH_CHECK,
    )
    Asserter.assert_equals(response.json.status, "fail")
    Asserter.assert_allin(
        response.json.checks,
        (
            "health_mongo",
            "health_redis",
            "health_sqlalchemy",
            "health_system",
            "health_services",
        ),
    )
    Asserter.assert_allin(
        response.json.checks.health_system.output,
        ("cpu", "disks", "mem", "nets", "swap", "errors"),
    )
    Asserter.assert_equals(response.json.checks.health_services.status, "fail")
    Asserter.assert_equals(
        response.json.checks.health_services.output["test-service-fail"].status, 500
    )
    Asserter.assert_equals(
        response.json.checks.health_services.output["test-service-pass"].status, 200
    )
