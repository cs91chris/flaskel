import flask

from flaskel import httpcode
from flaskel.views import Resource

resources = [
    {'item': 1},
    {'item': 2},
    {'item': 3},
]

sub_resources = [
    {'sub': 1}
]


class APIResource(Resource):
    def on_get(self, res_id):
        try:
            return resources[res_id - 1]
        except IndexError:
            flask.abort(httpcode.NOT_FOUND)

    def on_collection(self):
        return resources

    def on_post(self):
        resources.append(flask.request.get_json())
        return flask.request.get_json(), httpcode.CREATED

    def on_delete(self, res_id):
        resources.pop(res_id)

    def on_put(self, res_id):
        resources[res_id - 1] = flask.request.get_json()
        return resources[res_id - 1]

    def sub_items(self, res_id):
        try:
            return sub_resources[res_id - 1]
        except IndexError:
            return []

    def sub_items_post(self, res_id):
        sub_resources[res_id - 1] = flask.request.get_json()
        return sub_resources[res_id - 1], httpcode.CREATED
