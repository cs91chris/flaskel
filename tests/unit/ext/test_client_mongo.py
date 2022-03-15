from vbcore.datastruct import ObjectDict
from vbcore.tester.mixins import Asserter

from flaskel.ext.mongo import FlaskMongoDB


def test_init_app(flaskel_app):
    timeout = 1
    app = flaskel_app
    app.config.APP_NAME = "TEST_APP"
    app.config.MONGO_OPTS = ObjectDict(timeout=timeout)

    client_mongo = FlaskMongoDB()
    client_mongo.init_app(app)

    Asserter.assert_equals(app.extensions["mongo"]["default"], client_mongo)
    Asserter.assert_equals(app.config.MONGO_URI, "mongodb://localhost")
    Asserter.assert_equals(
        app.config.MONGO_OPTS,
        {
            "appname": app.config.APP_NAME,
            "directConnection": False,
            "minPoolSize": 0,
            "maxPoolSize": 100,
            "maxConnecting": 2,
            "retryWrites": True,
            "retryReads": True,
            "maxIdleTimeMS": None,
            "waitQueueTimeoutMS": None,
            "document_class": ObjectDict,
            "socketTimeoutMS": timeout,
            "connectTimeoutMS": timeout,
            "serverSelectionTimeoutMS": timeout,
            "heartbeatFrequencyMS": 10000,
        },
    )
