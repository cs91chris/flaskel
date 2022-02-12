import flask
from vbcore.http import httpcode, rpc

from flaskel.ext import auth
from flaskel.ext.auth import basic_auth
from flaskel.ext.sqlalchemy import db
from flaskel.utils.datastruct import ConfigProxy
from flaskel.utils.validator import PayloadValidator
from flaskel.views import Resource
from flaskel.views.resource import Restful
from flaskel.views.token import BaseTokenAuth


class BlackListToken(db.Model, auth.RevokedTokenMixin):
    __tablename__ = "revoked_tokens"


class TokenAuthView(BaseTokenAuth):
    handler = auth.DBTokenHandler(BlackListToken, db.session)


class ApiItem(Restful):
    post_schema = ConfigProxy("SCHEMAS.ITEM_POST")
    decorators = [basic_auth.login_required()]


class APIResource(Resource):
    def __init__(self):
        self.resources = [
            {"item": 1},
            {"item": 2},
            {"item": 3},
        ]

        self.sub_resources = [{"sub": 1}]

    def on_get(self, res_id, *_, **__):
        try:
            return self.resources[res_id - 1]
        except IndexError:
            flask.abort(httpcode.NOT_FOUND)
            return None

    def on_collection(self, *_, **__):
        return self.resources

    def on_post(self, *_, **__):
        payload = PayloadValidator.validate("ITEM_POST")
        return payload, httpcode.CREATED

    def on_delete(self, res_id, *_, **__):
        self.resources.pop(res_id)

    def on_put(self, res_id, *_, **__):
        self.resources[res_id - 1] = flask.request.json
        return self.resources[res_id - 1]

    def sub_items(self, res_id):
        try:
            return self.sub_resources[res_id - 1]
        except IndexError:
            return []

    def sub_items_post(self, res_id):
        self.sub_resources[res_id - 1] = flask.request.json
        return self.sub_resources[res_id - 1], httpcode.CREATED


class MyJsonRPC:
    def testAction1(self, **__):
        return {"action1": True}

    def testAction2(self, **__):
        return {"action2": True}

    def testInvalidParams(self, **kwargs):
        if kwargs.get("param") != "testparam":
            raise rpc.RPCInvalidParams()

    def testInternalError(self):
        raise ValueError
