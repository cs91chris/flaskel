from flask import Blueprint
from redislite import StrictRedis
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, rpc

from flaskel import ConfigProxy, PayloadValidator, abort
from flaskel.ext import auth, default
from flaskel.extra import apidoc
from flaskel.views import RenderTemplate
from flaskel.views.resource import Resource, Restful
from flaskel.views.static import StaticFileView as BaseStaticFileView, SPAView
from flaskel.views.token import BaseTokenAuth


class StaticFileView(BaseStaticFileView):
    default_view_name = "assets"
    default_static_path = "tests/integ/data/assets"
    default_urls = ("/assets/<path:filename>",)


class IndexTemplate(RenderTemplate):
    def service(self, *_, **kwargs):
        return ObjectDict(username="USERNAME", title="TITLE")


class ApiDocTemplate(apidoc.ApiDocTemplate):
    apispec_view = "apispec"


class TokenAuthView(BaseTokenAuth):
    handler = auth.RedisTokenHandler(redis=StrictRedis("/tmp/redis.db"))


class ApiItem(Restful):
    default_view_name = "resource_item"
    post_schema = ConfigProxy("SCHEMAS.ITEM_POST")
    put_schema = ConfigProxy("SCHEMAS.ITEM_POST")


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
    def action_success(**__):
        return {"action_success": "action_success"}

    @staticmethod
    def action_invalid_params(**kwargs):
        if kwargs.get("param") != "testparam":
            raise rpc.RPCInvalidParams()

    @staticmethod
    def action_error(**__):
        raise ValueError("value error")


bp_api = Blueprint(
    "api",
    __name__,
    subdomain="api",
    static_folder=None,
    static_url_path=None,
    template_folder=None,
)

bp_spa = Blueprint(
    "spa",
    __name__,
    template_folder=SPAView.default_template_folder,
    static_folder=SPAView.default_static_folder,
    static_url_path=SPAView.default_static_url_path,
)

bp_web = Blueprint(
    "web",
    __name__,
    url_prefix="/",
    template_folder="data/templates",
    static_folder="data/assets",
    static_url_path="/assets/",
)

default.cors.init_app(bp_api)
default.error_handler.api_register(bp_api)
default.error_handler.web_register(bp_spa)
default.error_handler.web_register(bp_web)
