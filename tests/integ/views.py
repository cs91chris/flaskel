from unittest.mock import MagicMock

from vbcore.http import httpcode, rpc

from flaskel import ConfigProxy, PayloadValidator, abort
from flaskel.ext import auth
from flaskel.extra import apidoc
from flaskel.views.resource import Resource, Restful
from flaskel.views.token import BaseTokenAuth


class VIEWS:
    check_token = "api.token_check"
    access_token = "api.token_access"
    refresh_token = "api.token_refresh"
    revoke_token = "api.token_revoke"
    api_docs = "apidocs"
    api_specs = "apispec"


class ApiDocTemplate(apidoc.ApiDocTemplate):
    apispec_view = "apispec"


class TokenAuthView(BaseTokenAuth):
    # TODO use a fake redis client instead of a mock
    handler = auth.RedisTokenHandler(redis=MagicMock())


class ApiItem(Restful):
    post_schema = ConfigProxy("SCHEMAS.ITEM_POST")
    decorators = [auth.basic_auth.login_required()]


class APIResource(Resource):
    default_view_name: str = "resources"
    default_urls = ("/resources",)

    resources = [
        {"id": 1, "item": "1"},
        {"id": 2, "item": "2"},
        {"id": 3, "item": "3"},
    ]

    def on_get(self, res_id, *_, **__):
        try:
            return self.resources[res_id - 1]
        except IndexError:
            return abort(httpcode.NOT_FOUND)

    def on_collection(self, *_, **__):
        return self.resources

    def on_post(self, *_, **__):
        payload = PayloadValidator.validate("ITEM_POST")
        data = {"id": len(self.resources) + 1, **payload}
        self.resources.append(data)
        return data, httpcode.CREATED

    def on_delete(self, res_id, *_, **__):
        try:
            del self.resources[res_id - 1]
        except IndexError:
            abort(httpcode.NOT_FOUND)

    def on_put(self, res_id, *_, **__):
        payload = PayloadValidator.validate("ITEM")
        try:
            self.resources[res_id - 1] = payload
            return payload
        except IndexError:
            return abort(httpcode.NOT_FOUND)


class MyJsonRPC:
    @staticmethod
    def test_action_1(**__):
        return {"action1": True}

    @staticmethod
    def test_action_2(**__):
        return {"action2": True}

    @staticmethod
    def test_invalid_params(**kwargs):
        if kwargs.get("param") != "testparam":
            raise rpc.RPCInvalidParams()

    @staticmethod
    def test_internal_error():
        raise ValueError
