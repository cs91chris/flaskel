from vbcore.tester.mixins import Asserter

from flaskel.ext.default import client_mongo


def test_init_app(flaskel_app):
    app = flaskel_app
    client_mongo.init_app(app)

    Asserter.assert_equals(app.extensions["mongo"]["default"], client_mongo)
    Asserter.assert_equals(app.config.MONGO_URI, "mongodb://localhost")
    Asserter.assert_equals(
        app.config.MONGO_OPTS,
        {
            "connectTimeoutMS": 1000,
            "serverSelectionTimeoutMS": 1000,
        },
    )
