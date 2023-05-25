import sqlalchemy as sa
from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.jsonschema.support import Fields
from vbcore.tester.asserter import Asserter

from flaskel.ext.default import Database
from flaskel.tester.helpers import ApiTester, config, url_for
from flaskel.utils.schemas.default import SCHEMAS
from flaskel.views.resource import CatalogResource
from tests.integ.views import ApiItem, APIResource, bp_api

db = Database()


class Item(db.Model, StandardMixin):
    __tablename__ = "items"

    item = sa.Column(sa.String(100), nullable=False)

    def to_dict(self, **__):
        return ObjectDict(id=self.id, item=self.item)


ITEM_SCHEMAS = ObjectDict(
    API_PROBLEM=SCHEMAS.API_PROBLEM,
    ITEM_POST=Fields.object(
        properties={"item": Fields.string},
    ),
    ITEM=Fields.object(properties={"id": Fields.integer, "item": Fields.string}),
    ITEM_LIST=Fields.array_object(
        properties={"id": Fields.integer, "item": Fields.string}
    ),
)


def test_api_resource(testapp):
    app = testapp(
        config=ObjectDict(SCHEMAS=ITEM_SCHEMAS), views=((APIResource, bp_api),)
    )
    client = ApiTester(app.test_client())

    client.restful(
        view="api.resources",
        schema_read=config.SCHEMAS.ITEM,
        schema_collection=config.SCHEMAS.ITEM_LIST,
        body_create={"item": "TEST"},
        body_update={"id": 1, "item": "TEST"},
    )


def test_catalog(testapp, session_save):
    view = "api.resource"

    app = testapp(
        config=ObjectDict(SCHEMAS=ITEM_SCHEMAS),
        extensions={"database": db},
        views=((CatalogResource, bp_api, {"model": Item}),),
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)

    with app.app_context():
        session_save(
            [
                Item(id=1, item="item-1"),
                Item(id=2, item="item-2"),
                Item(id=3, item="item-3"),
            ]
        )

    client.get(
        url=url_for(view, res_id=1),
        schema=config.SCHEMAS.ITEM,
    )
    client.get(
        url=url_for(view, res_id=4),
        status=httpcode.NOT_FOUND,
        schema=config.SCHEMAS.API_PROBLEM,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )

    response = client.get(
        view=view,
        schema=config.SCHEMAS.ITEM_LIST,
    )
    Asserter.assert_greater(len(response.json), 0)


def test_restful(testapp, session_save):
    app = testapp(
        config=ObjectDict(SCHEMAS=ITEM_SCHEMAS, PAGINATION_MAX_PAGE_SIZE=3),
        extensions={"database": db},
        views=((ApiItem, bp_api, {"model": Item}),),
    )
    client = ApiTester(app.test_client())

    with app.app_context():
        session_save([Item(id=i, item=f"item-{i}") for i in range(1, 3 * 3)])

    client.restful(
        view="api.resource_item",
        schema_read=config.SCHEMAS.ITEM,
        schema_collection=config.SCHEMAS.ITEM_LIST,
        body_create={"item": "TEST CREATE"},
        body_update={"item": "TEST CREATE"},
    )
