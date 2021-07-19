import json
import logging

from flaskel import httpcode
from flaskel.http import FlaskelHTTPDumper
from flaskel.utils.schemas.default import SCHEMAS
from .helpers import basic_auth_header
from .mixins import JSONValidatorMixin, RegexMixin

__all__ = [
    "TestHttpApi",
    "TestHttpCall",
    "TestJsonRPC",
    "TestRestApi",
]


class TestHttpCall(FlaskelHTTPDumper, JSONValidatorMixin, RegexMixin):
    __test__ = False
    default_status_code = (httpcode.SUCCESS, 299)
    default_content_type = "text/html"

    def __init__(self, test_client, endpoint=None, auth=None, **__):
        """

        :param endpoint:
        :param auth:
        :param kwargs:
        """
        self.auth = None
        self.response = None
        self.endpoint = endpoint
        self.test_client = test_client
        self.log = logging.getLogger()

        if auth:
            self.set_auth(auth)

    def set_url(self, url):
        """

        :param url:
        """
        if not url.startswith("http"):
            self.endpoint = "/".join([self.endpoint.rstrip("/"), url.lstrip("/")])
        else:
            self.endpoint = url

    def set_auth(self, config):
        """

        :param config:
        """
        config = config or {}
        auth_type = config.get("type")
        if auth_type == "basic" and config.get("username"):
            password = config.get("password") or config["username"]
            self.auth = basic_auth_header(config.get("username"), password)

    def assert_status_code(self, code, in_range=False, is_in=False):
        """

        :param code:
        :param in_range:
        :param is_in:
        """
        status_code = self.response.status_code
        if type(code) in (list, tuple):
            if in_range:
                self.assert_range(status_code, code)
            if is_in:
                self.assert_in(status_code, code)
        else:
            self.assert_equals(status_code, code)

    def assert_header(self, name, value, is_in=False, regex=False):
        """

        :param name:
        :param value:
        :param is_in:
        :param regex:
        """
        header = self.response.headers.get(name)
        if is_in:
            self.assert_in(header, value)
        elif regex:
            self.assert_match(header, value)
        else:
            self.assert_equals(header, value)

    def assert_response(self, **kwargs):
        """

        :param kwargs:
        """
        code = kwargs.get("status") or {
            "code": self.default_status_code,
            "in_range": True,
        }
        headers = kwargs.get("headers") or {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = {
                "value": rf"{self.default_content_type}*",
                "regex": True,
            }

        self.assert_status_code(**code)
        for k, v in headers.items():
            if v is not None:
                self.assert_header(name=k, **v)

    def request(self, method="GET", url=None, **kwargs):
        """

        :param method:
        :param url:
        :param kwargs:
        :return:
        """
        url = url or self.endpoint
        if not url.startswith("http"):
            url = "{}{}".format(self.endpoint, url)

        self.set_auth(kwargs.pop("auth", None))
        if self.auth is not None:
            kwargs["auth"] = self.auth

        self.response = self.test_client.open(method=method, path=url, **kwargs)
        self.dump_response(self.response, dump_body=True)

    def perform(self, request, response=None, **__):
        """

        :param request:
        :param response:
        """
        self.request(**request)
        self.assert_response(**(response or {}))


class TestHttpApi(TestHttpCall):
    default_content_type = "application/json"

    @property
    def json(self):
        try:
            if self.response.status_code != httpcode.NO_CONTENT and "json" in (
                self.response.headers.get("Content-Type") or ""
            ):
                return self.response.get_json()
        except json.decoder.JSONDecodeError as exc:
            assert False, "Test that json is valid failed, got: {}".format(exc)
        return None

    def assert_response(self, **kwargs):
        """

        :param kwargs:
        """
        super().assert_response(**kwargs)
        if kwargs.get("schema") is not None:
            self.assert_schema(self.json, kwargs.get("schema"))


class TestJsonRPC(TestHttpApi):
    version = "2.0"
    default_schema = SCHEMAS.JSONRPC.response

    # noinspection PyShadowingBuiltins
    @classmethod
    def prepare_payload(
        cls, id=False, method=None, params=None
    ):  # pylint: disable=W0622
        """

        :param id:
        :param method:
        :param params:
        :return:
        """
        data = dict(jsonrpc=cls.version, method=method)
        if id is not False:
            data["id"] = id
        if params:
            data["params"] = params
        return data

    def perform(self, request, response=None, **__):
        """

        :param request:
        :param response:
        """
        req = {"method": "POST"}
        res = response or {}
        res.setdefault("schema", self.default_schema)

        if type(request) in (list, tuple):
            req["json"] = [self.prepare_payload(*a) for a in request]
        else:
            req["json"] = self.prepare_payload(**request)

        super().perform(request=req, response=res)


class TestRestApi(TestHttpApi):
    def __init__(self, *args, resource=None, res_id=None, **kwargs):
        """

        :param resource:
        :param res_id: resource id key
        """
        super().__init__(*args, **kwargs)
        self.res_id = res_id or "id"
        self.set_resource(resource)

    def set_resource(self, resource, res_id=None):
        """

        :param resource:
        :param res_id:
        """
        self.res_id = res_id or self.res_id
        if resource:
            self.endpoint = f"{self.endpoint}/{resource}"

    def resource_url(self, res_id):
        """

        :param res_id:
        :return:
        """
        return f"{self.endpoint}/{res_id}"

    def _normalize(self, request, response, method="GET", url=None):
        """

        :param request:
        :param response:
        :param method:
        :param url:
        :return:
        """
        request = request or {}
        response = response or {}
        request["method"] = method
        request["url"] = url or self.endpoint
        return request, response

    def test_collection(self, request=None, response=None):
        req, res = self._normalize(request, response)
        res.setdefault(
            "status",
            dict(code=(httpcode.SUCCESS, httpcode.PARTIAL_CONTENT), is_in=True),
        )
        self.perform(req, res)

    def test_post(self, request=None, response=None):
        req, res = self._normalize(request, response, "POST")
        res.setdefault("status", dict(code=httpcode.CREATED))
        self.perform(req, res)

    def test_get(self, res_id, request=None, response=None):
        req, res = self._normalize(request, response, url=self.resource_url(res_id))
        self.perform(req, res)

    def test_put(self, res_id, request=None, response=None):
        req, res = self._normalize(request, response, "PUT", self.resource_url(res_id))
        self.perform(req, res)

    def test_delete(self, res_id, request=None, response=None):
        req, res = self._normalize(
            request, response, "DELETE", self.resource_url(res_id)
        )
        res.setdefault("status", dict(code=httpcode.NO_CONTENT))
        res.setdefault("headers", {})
        res["headers"]["Content-Type"] = None
        self.perform(req, res)
