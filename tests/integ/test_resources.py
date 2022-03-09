from vbcore.datastruct import ObjectDict
from vbcore.jsonschema.support import Fields

from flaskel.tester.helpers import ApiTester, config
from tests.integ.views import APIResource


def test_api_resource(testapp):
    conf = ObjectDict(
        SCHEMAS=ObjectDict(
            ITEM_POST=Fields.object(
                properties={"item": Fields.string},
            ),
            ITEM=Fields.object(
                properties={"id": Fields.integer, "item": Fields.string}
            ),
            ITEM_LIST=Fields.array_object(
                properties={"id": Fields.integer, "item": Fields.string}
            ),
        )
    )
    app = testapp(config=conf, views=(APIResource,))
    client = ApiTester(app.test_client())

    client.restful(
        view="resources",
        schema_read=config.SCHEMAS.ITEM,
        schema_collection=config.SCHEMAS.ITEM_LIST,
        body_create={"item": "TEST"},
        body_update={"id": 1, "item": "TEST"},
    )


def test_catalog(testapp):
    # TODO: added missing tests
    assert True


def test_restful(testapp):
    # TODO: added missing tests
    assert True
