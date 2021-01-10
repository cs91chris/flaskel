import os
from functools import partial

import flask
import werkzeug.exceptions

from flaskel import http, httpcode
from flaskel.http import batch, rpc, useragent
from flaskel.tester import Asserter
from flaskel.utils import datastruct, date, uuid, SCHEMAS
from flaskel.utils.yaml import setup_yaml_parser
# noinspection PyUnresolvedReferences
from . import app_dev, app_prod, testapp

setup_yaml_parser()

url_for = partial(flask.url_for, _external=True)

CTS = datastruct.ObjectDict(
    json='application/json',
    xml='application/xml',
    html='text/html',
    json_problem='application/problem+json',
    xml_problem='application/problem+xml',
    json_health='application/health+json',
)

HOSTS = datastruct.ObjectDict(
    apitester="http://httpbin.org",
    fake="http://localhost"
)


def test_app_dev(app_dev):
    client = app_dev.test_client()
    res = client.get(flask.url_for('web.index'))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.html)
    Asserter.assert_equals(app_dev.config.FLASK_ENV, 'development')
    Asserter.assert_equals(app_dev.config.SECRET_KEY, 'fake_very_complex_string')

    res = client.get(url_for('test.test_https'))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.scheme, 'http')
    Asserter.assert_true(res.json.url_for.startswith('http'))


def test_api_resources(testapp):
    res = testapp.get(url_for('api.resource_api'), headers={'Accept': CTS.xml})
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.xml)

    res = testapp.get(url_for('api.resource_api', res_id=1))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.json)

    res = testapp.get(url_for('api.resource_api', res_id=1, sub_resource='items'))
    Asserter.assert_status_code(res)
    Asserter.assert_content_type(res, CTS.json)

    res = testapp.get(url_for('api.resource_api', res_id=1, sub_resource='not-found'))
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.json_problem)
    Asserter.assert_schema(res.json, SCHEMAS.API_PROBLEM)

    res = testapp.delete(url_for('api.resource_api', res_id=1))
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)

    data = dict(item='test')
    res = testapp.put(url_for('api.resource_api', res_id=1), json=data)
    Asserter.assert_status_code(res)

    res = testapp.post(url_for('api.resource_api'), json=data)
    Asserter.assert_status_code(res, httpcode.CREATED)

    res = testapp.post(url_for('api.resource_api', res_id=1, sub_resource='items'), json=data)
    Asserter.assert_status_code(res, httpcode.CREATED)


def test_api_cors(testapp):
    res = testapp.get(url_for('api.resource_api'))
    Asserter.assert_header(res, 'Access-Control-Allow-Origin', '*')


def test_dispatch_error_web(testapp):
    res = testapp.get('/web-page-not-found')
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.html)


def test_dispatch_error_api(testapp):
    res = testapp.get(f"http://api.{testapp.application.config.SERVER_NAME}/not_found")
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.json_problem)
    Asserter.assert_schema(res.json, SCHEMAS.API_PROBLEM)


def test_force_https(testapp):
    res = testapp.get(url_for('test.test_https'))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.scheme, 'https')
    Asserter.assert_true(res.json.url_for.startswith('https'))


def test_reverse_proxy(testapp):
    res = testapp.get(url_for('test.test_proxy'), headers={
        'X-Forwarded-Prefix': '/test'
    })
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.script_name, '/test')
    Asserter.assert_equals(res.json.original.SCRIPT_NAME, '')


def test_secret_key_prod(testapp):
    Asserter.assert_equals(testapp.application.config.FLASK_ENV, 'production')
    Asserter.assert_true(os.path.isfile('.secret.key'))
    os.remove('.secret.key')


def test_method_override(testapp):
    res = testapp.post(
        url_for('test.method_override_post'),
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    Asserter.assert_status_code(res)

    res = testapp.post(url_for('test.method_override_post') + '?_method_override=PUT')
    Asserter.assert_status_code(res)


def test_converters(testapp):
    res = testapp.get(url_for('test.list_converter', data=['a', 'b', 'c']))
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json, 3)


def test_utils_get_json(testapp):
    res = testapp.post(url_for('test.get_invalid_json'))
    Asserter.assert_status_code(res, httpcode.BAD_REQUEST)


def test_utils_send_file(testapp):
    filename = 'MANIFEST.in'
    url = url_for('test.download') + "?filename={}"

    res = testapp.get(url.format(filename))
    Asserter.assert_status_code(res)
    Asserter.assert_header(res, 'Content-Disposition', f'attachment; filename={filename}')
    Asserter.assert_header(res, 'X-Accel-Redirect', f'./{filename}')
    Asserter.assert_true(res.headers.get('X-Sendfile').endswith(f'./{filename}'))
    Asserter.assert_equals(res.data, b'')

    res = testapp.get(url.format('nofile.txt'))
    Asserter.assert_status_code(res, httpcode.NOT_FOUND)
    Asserter.assert_content_type(res, CTS.html)


def test_utils_uuid(testapp):
    res = testapp.get(url_for('test.return_uuid'))
    Asserter.assert_false(uuid.check_uuid('fake uuid'))
    Asserter.assert_true(uuid.check_uuid(uuid.get_uuid(hexify=False)))
    Asserter.assert_true(uuid.check_uuid(res.json.get('uuid1'), ver=1))
    Asserter.assert_true(uuid.check_uuid(res.json.get('uuid3'), ver=3))
    Asserter.assert_true(uuid.check_uuid(res.json.get('uuid4')))
    Asserter.assert_true(uuid.check_uuid(res.json.get('uuid5'), ver=5))


def test_crypto(testapp):
    passwd = 'my-favourite-password'
    crypto = testapp.application.extensions['argon2']
    res = testapp.get(url_for('test.crypt', passwd=passwd))
    Asserter.assert_true(crypto.verify_hash(res.data, passwd))
    Asserter.assert_false(crypto.verify_hash(res.data, "wrong-pass"))


def test_utils_http_client_simple(testapp):
    with testapp.application.test_request_context():
        api = http.FlaskelHttp(HOSTS.apitester, token='pippo', logger=testapp.application.logger)
        res = api.delete('/status/202')
        Asserter.assert_equals(res.status, httpcode.ACCEPTED)
        res = api.patch('/status/400')
        Asserter.assert_equals(res.status, httpcode.BAD_REQUEST)


def test_utils_http_client_exception(testapp):
    logger = testapp.application.logger
    api = http.HTTPClient(HOSTS.apitester, token='pippo', raise_on_exc=True, logger=logger)
    fake_api = http.HTTPClient(HOSTS.fake, username='test', password='test', logger=logger)

    res = fake_api.put('/', timeout=0.1)
    Asserter.assert_equals(res.status, httpcode.SERVICE_UNAVAILABLE)
    try:
        api.request('/status/500', 'PUT')
    except http.client.http_exc.HTTPError as exc:
        Asserter.assert_equals(exc.response.status_code, httpcode.INTERNAL_SERVER_ERROR)
    try:
        fake_api.request('/', timeout=0.1)
    except werkzeug.exceptions.HTTPException as exc:
        Asserter.assert_equals(exc.code, httpcode.INTERNAL_SERVER_ERROR)


def test_utils_http_client_filename(testapp):
    filename = "pippo.txt"
    hdr = 'Content-Disposition'
    param = {hdr: None}

    api = http.HTTPClient(HOSTS.apitester, logger=testapp.application.logger)

    param[hdr] = f"attachment; filename={filename}"
    res = api.get('/response-headers', params=param)
    Asserter.assert_equals(api.response_filename(res.headers), filename)

    param[hdr] = f"filename={filename}"
    res = api.post('/response-headers', params=param)
    Asserter.assert_equals(api.response_filename(res.headers), filename)

    param[hdr] = filename
    res = api.post('/response-headers', params=param)
    Asserter.assert_none(api.response_filename(res.headers))


def test_http_client_batch(testapp):
    responses = batch.HTTPBatchRequests(logger=testapp.application.logger).request([
        dict(url=f"{HOSTS.apitester}/anything", method="GET", headers={"HDR1": "HDR1"}),
        dict(url=f"{HOSTS.apitester}/status/{httpcode.NOT_FOUND}", method="GET"),
        dict(url=HOSTS.fake, method='GET', timeout=0.1),
    ])
    Asserter.assert_equals(responses[0].body.headers.Hdr1, 'HDR1')
    Asserter.assert_equals(responses[1].status, httpcode.NOT_FOUND)
    Asserter.assert_equals(responses[2].status, httpcode.SERVICE_UNAVAILABLE)


def test_utils_http_jsonrpc_client(testapp):
    params = dict(a=1, b=2)
    api = http.JsonRPCClient(HOSTS.apitester, "/anything", logger=testapp.application.logger)
    res = api.request('method.test', params=params)
    Asserter.assert_equals(res.json.jsonrpc, '2.0')
    Asserter.assert_equals(res.json.id, api.request_id)
    Asserter.assert_equals(res.json.params, params)


def test_healthcheck(testapp):
    res = testapp.get(testapp.application.config.HEALTHCHECK_PATH)
    Asserter.assert_status_code(res, httpcode.SERVICE_UNAVAILABLE)
    Asserter.assert_content_type(res, CTS.json_health)
    Asserter.assert_schema(res.json, SCHEMAS.HEALTHCHECK)


def test_api_jsonrpc_success(testapp):
    call_id = 1
    url = url_for('api.myJsonRPC')

    res = testapp.jsonrpc(url, method="MyJsonRPC.testAction1", call_id=call_id)
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.id, call_id)
    Asserter.assert_true(res.json.result.action1)

    res = testapp.jsonrpc(url, method="MyJsonRPC.testAction2")
    Asserter.assert_status_code(res, httpcode.NO_CONTENT)


def test_api_jsonrpc_error(testapp):
    call_id = 1
    url = url_for('api.myJsonRPC')

    res = testapp.jsonrpc(url, method="NotFoundMethod", call_id=call_id)
    Asserter.assert_status_code(res)
    Asserter.assert_equals(res.json.error.code, rpc.RPCMethodNotFound().code)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.id, call_id)
    Asserter.assert_true(res.json.error.message)

    res = testapp.jsonrpc(url, json={})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.error.code, rpc.RPCParseError().code)

    res = testapp.jsonrpc(url, json={"params": None})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = testapp.jsonrpc(url, json={"jsonrpc": 1, 'method': "MyJsonRPC.testAction1"})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidRequest().code)

    res = testapp.jsonrpc(url, method="MyJsonRPC.testInternalError", call_id=call_id)
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInternalError().code)


def test_api_jsonrpc_params(testapp):
    url = url_for('api.myJsonRPC')
    method = "MyJsonRPC.testInvalidParams"

    res = testapp.jsonrpc(url, method=method, call_id=1, params={"param": "testparam"})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_not_in('error', res.json)

    res = testapp.jsonrpc(url, method=method, call_id=1, params={"params": None})
    Asserter.assert_status_code(res)
    Asserter.assert_schema(res.json, SCHEMAS.JSONRPC_RESPONSE)
    Asserter.assert_equals(res.json.error.code, rpc.RPCInvalidParams().code)


def test_useragent(testapp):
    res = testapp.get(url_for('test.useragent'))
    Asserter.assert_status_code(res)
    Asserter.assert_allin(res.json.keys(), ('browser', 'device', 'os', 'raw'))
    ua_string = """
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) 
        Chrome/70.0.3538.77 Safari/537.36
    """
    res = useragent.UserAgent().parse(ua_string)
    Asserter.assert_equals(res.raw, ua_string)


def test_utils_date_conversion():
    exc = False
    fmt = "%d %B %Y %I:%M %p"
    iso_date = '2020-12-28T19:53:00'
    not_iso_date = '28 December 2020 07:53 PM'
    invalid_date = 'invalid_date'

    res = date.from_iso_format(iso_date, fmt, exc=exc)
    Asserter.assert_true(res)
    Asserter.assert_equals(not_iso_date, res)

    res = date.to_iso_format(not_iso_date, fmt, exc=exc)
    Asserter.assert_true(res)
    Asserter.assert_equals(iso_date, res)

    Asserter.assert_none(date.from_iso_format(invalid_date, fmt, exc=exc))
    Asserter.assert_none(date.to_iso_format(invalid_date, fmt, exc=exc))


def test_correlation_id(testapp):
    cap = testapp.application
    request_id_header = cap.config.REQUEST_ID_HEADER

    res = testapp.get('/')
    Asserter.assert_header(res, request_id_header, is_in=True)
    Asserter.assert_type(res.headers[request_id_header], str)

    req_id = uuid.get_uuid()
    res = testapp.get('/', headers={request_id_header: req_id})
    Asserter.assert_header(res, request_id_header, req_id)

    req_id = 'invalid_req_id'
    res = testapp.get('/', headers={request_id_header: req_id})
    Asserter.assert_different(res.headers[request_id_header], req_id)
