from vbcore.http import httpcode, rpc
from vbcore.tester.http import TestJsonRPC
from vbcore.tester.mixins import Asserter

from flaskel.tester.helpers import url_for
from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS
from flaskel.views.rpc import JSONRPCView


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


JSONRPCView.load_from_object(MyJsonRPC())
ACTION_SUCCESS = "MyJsonRPC.action_success"
ACTION_NOT_FOUND = "MyJsonRPC.NotFoundMethod"


def test_api_jsonrpc_success(testapp):
    app = testapp(views=(JSONRPCView,))

    call_id = 1
    url = url_for("jsonrpc")
    client = app.test_client()

    rpc_client = TestJsonRPC(client, endpoint=url)
    rpc_client.perform(request=dict(method=ACTION_SUCCESS, id=call_id))
    Asserter.assert_equals(rpc_client.json.id, call_id)
    Asserter.assert_equals(rpc_client.json.result.action_success, "action_success")

    res = client.jsonrpc(url, method=ACTION_SUCCESS)
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)


def test_api_jsonrpc_error(testapp):
    app = testapp(views=(JSONRPCView,))

    call_id = 1
    url = url_for("jsonrpc")
    client = app.test_client()

    response_schema = DEFAULT_SCHEMAS.JSONRPC.RESPONSE

    res = client.jsonrpc(url, method="NotFoundMethod", call_id=call_id)
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.error.code, rpc.RPCMethodNotFound().code)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.id, call_id)
    Asserter.assert_true(res.json.error.message)

    res = client.jsonrpc(url, json={})
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.error.code, rpc.RPCParseError().code)

    res = client.jsonrpc(url, json={"params": None})
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = client.jsonrpc(url, json={"jsonrpc": 1, "method": ACTION_SUCCESS})
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = client.jsonrpc(url, method="MyJsonRPC.action_error", call_id=call_id)
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInternalError().code)


def test_api_jsonrpc_params(testapp):
    app = testapp(views=(JSONRPCView,))
    url = url_for("jsonrpc")
    client = app.test_client()

    method = "MyJsonRPC.action_invalid_params"
    response_schema = DEFAULT_SCHEMAS.JSONRPC.RESPONSE

    res = client.jsonrpc(url, method=method, call_id=1, params={"param": "testparam"})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_not_in("error", res.json)

    res = client.jsonrpc(url, method=method, call_id=1, params={"params": None})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, response_schema)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidParams().code)


def test_api_jsonrpc_batch(testapp):
    app = testapp(views=(JSONRPCView,))
    app.config.JSONRPC_BATCH_MAX_REQUEST = 2
    url = url_for("jsonrpc")
    client = app.test_client()

    res = client.jsonrpc_batch(
        url,
        requests=(
            dict(method=ACTION_SUCCESS, call_id=1, params={}),
            dict(method=ACTION_NOT_FOUND, call_id=2),
        ),
    )
    Asserter.assert_status_code(res, httpcode.MULTI_STATUS)
    Asserter.assert_equals(res.json[0].result.action_success, "action_success")
    Asserter.assert_equals(res.json[1].error.code, rpc.RPCMethodNotFound().code)

    res = client.jsonrpc_batch(
        url,
        requests=(
            dict(method=ACTION_SUCCESS, call_id=1, params={}),
            dict(method=ACTION_NOT_FOUND, call_id=2),
            dict(method=ACTION_NOT_FOUND, call_id=3),
        ),
    )
    Asserter.assert_status_code(res, httpcode.REQUEST_ENTITY_TOO_LARGE)


def test_api_jsonrpc_notification(testapp):
    app = testapp(views=(JSONRPCView,))
    url = url_for("jsonrpc")
    client = app.test_client()

    res = client.jsonrpc_batch(
        url,
        requests=(
            dict(method=ACTION_SUCCESS, params={}),
            dict(method=ACTION_NOT_FOUND),
        ),
    )
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    res = client.jsonrpc_batch(
        url,
        requests=(
            dict(method=ACTION_SUCCESS, call_id=1, params={}),
            dict(method=ACTION_NOT_FOUND),
        ),
    )
    Asserter.assert_status_code(res)
    Asserter.assert_equals(len(res.json), 1)
