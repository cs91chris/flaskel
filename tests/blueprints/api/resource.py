import flask

from flaskel import httpcode
from flaskel.utils.schemas import PayloadValidator
from flaskel.views import Resource

resources = [
    {"item": 1},
    {"item": 2},
    {"item": 3},
]

sub_resources = [{"sub": 1}]


# pylint: disable=no-self-use
class APIResource(Resource):
    def on_get(self, res_id, *_, **__):
        try:
            return resources[res_id - 1]
        except IndexError:
            flask.abort(httpcode.NOT_FOUND)
            return None

    def on_collection(self, *_, **__):
        return resources

    def on_post(self, *_, **__):
        payload = PayloadValidator.validate("ITEM_POST")
        return payload, httpcode.CREATED

    def on_delete(self, res_id, *_, **__):
        resources.pop(res_id)

    def on_put(self, res_id, *_, **__):
        resources[res_id - 1] = flask.request.json
        return resources[res_id - 1]

    def sub_items(self, res_id):
        try:
            return sub_resources[res_id - 1]
        except IndexError:
            return []

    def sub_items_post(self, res_id):
        sub_resources[res_id - 1] = flask.request.json
        return sub_resources[res_id - 1], httpcode.CREATED
