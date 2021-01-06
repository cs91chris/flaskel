import os

import flask
import werkzeug.exceptions

from flaskel import http, httpcode
from flaskel.http import batch, rpc, useragent
from flaskel.tester import Asserter, HttpAsserter
from flaskel.utils import datastruct, date, uuid
from flaskel.utils.yaml import setup_yaml_parser
# noinspection PyUnresolvedReferences
from . import app_dev, app_prod, testapp

setup_yaml_parser()

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
    HttpAsserter.assert_status_code(client.get('/'))
    Asserter.assert_equals(app_dev.config.FLASK_ENV, 'development')
    Asserter.assert_equals(app_dev.config.SECRET_KEY, 'fake_very_complex_string')

    res = client.get('/test_https', base_url='http://' + app_dev.config.SERVER_NAME)
    HttpAsserter.assert_status_code(res)
    data = datastruct.ObjectDict(res.get_json())
    Asserter.assert_equals(data.scheme, 'http')
    Asserter.assert_true(data.url_for.startswith('http'))


def test_app_runs(testapp):
    res = testapp.get('/')
    HttpAsserter.assert_status_code(res)


def test_app_return_html(testapp):
    res = testapp.get('/web')
    HttpAsserter.assert_header(res, 'Content-Type', CTS.html, is_in=True)


def test_app_returns_json(testapp):
    res = testapp.get('/', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    HttpAsserter.assert_status_code(res, httpcode.NOT_FOUND)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json_problem, is_in=True)


def test_api_resources(testapp):
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.get('/resources', base_url=base_url, headers={'Accept': CTS.xml})
    HttpAsserter.assert_status_code(res)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.xml, is_in=True)

    res = testapp.get('/resources/1', base_url=base_url)
    HttpAsserter.assert_status_code(res)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json, is_in=True)

    res = testapp.get('/resources/1/items', base_url=base_url)
    HttpAsserter.assert_status_code(res)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json, is_in=True)

    res = testapp.get('/resources/1/not-found', base_url=base_url)
    HttpAsserter.assert_status_code(res, httpcode.NOT_FOUND)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json_problem, is_in=True)

    res = testapp.delete('/resources/1', base_url=base_url)
    HttpAsserter.assert_status_code(res, httpcode.NO_CONTENT)

    data = dict(item='test')
    res = testapp.put('/resources/1', json=data, base_url=base_url)
    HttpAsserter.assert_status_code(res)

    res = testapp.post('/resources', json=data, base_url=base_url)
    HttpAsserter.assert_status_code(res, httpcode.CREATED)

    res = testapp.post('/resources/1/items', json=data, base_url=base_url)
    HttpAsserter.assert_status_code(res, httpcode.CREATED)


def test_api_cors(testapp):
    res = testapp.get('/resources', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    HttpAsserter.assert_header(res, 'Access-Control-Allow-Origin', '*')


def test_dispatch_error_web(testapp):
    res = testapp.get('/web-page-not-found')
    HttpAsserter.assert_status_code(res, httpcode.NOT_FOUND)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.html, is_in=True)


def test_dispatch_error_api(testapp):
    res = testapp.get('/api-not-found', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    HttpAsserter.assert_status_code(res, httpcode.NOT_FOUND)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json_problem, is_in=True)


def test_force_https(testapp):
    res = testapp.get('/test_https', base_url='http://' + testapp.application.config.SERVER_NAME)
    HttpAsserter.assert_status_code(res)
    data = datastruct.ObjectDict(res.get_json())
    Asserter.assert_equals(data.scheme, 'https')
    Asserter.assert_true(data.url_for.startswith('https'))


def test_reverse_proxy(testapp):
    res = testapp.get('/proxy', headers={
        'X-Forwarded-Prefix': '/test'
    })
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.script_name, '/test')
    Asserter.assert_equals(data.original.SCRIPT_NAME, '')


def test_secret_key_prod(testapp):
    Asserter.assert_equals(testapp.application.config.FLASK_ENV, 'production')
    Asserter.assert_true(os.path.isfile('.secret.key'))
    os.remove('.secret.key')


def test_method_override(testapp):
    res = testapp.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    HttpAsserter.assert_status_code(res)

    res = testapp.post('/method_override?_method_override=PUT')
    HttpAsserter.assert_status_code(res)


def test_converters(testapp):
    res = testapp.get('/list/a-b-c')
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(res.get_json(), 3)


def test_utils_get_json(testapp):
    res = testapp.post('/invalid-json')
    HttpAsserter.assert_status_code(res, httpcode.BAD_REQUEST)


def test_utils_send_file(testapp):
    filename = 'MANIFEST.in'
    res = testapp.get(f'/download?filename={filename}')
    HttpAsserter.assert_status_code(res)
    HttpAsserter.assert_header(res, 'Content-Disposition', f'attachment; filename={filename}')
    HttpAsserter.assert_header(res, 'X-Accel-Redirect', f'./{filename}')
    Asserter.assert_true(res.headers.get('X-Sendfile').endswith(f'./{filename}'))
    Asserter.assert_equals(res.data, b'')

    res = testapp.get('/download?filename=nofile.txt')
    HttpAsserter.assert_status_code(res, httpcode.NOT_FOUND)


def test_utils_uuid(testapp):
    res = testapp.get('/uuid')
    data = res.get_json()
    Asserter.assert_false(uuid.check_uuid('fake uuid'))
    Asserter.assert_true(uuid.check_uuid(uuid.get_uuid(hexify=False)))
    Asserter.assert_true(uuid.check_uuid(data.get('uuid1'), ver=1))
    Asserter.assert_true(uuid.check_uuid(data.get('uuid3'), ver=3))
    Asserter.assert_true(uuid.check_uuid(data.get('uuid4')))
    Asserter.assert_true(uuid.check_uuid(data.get('uuid5'), ver=5))


def test_crypto(testapp):
    passwd = 'my-favourite-password'
    crypto = testapp.application.extensions['argon2']
    res = testapp.get(f'/crypt/{passwd}')
    Asserter.assert_true(crypto.verify_hash(res.data, passwd))
    Asserter.assert_false(crypto.verify_hash(res.data, "wrong-pass"))


def test_utils_http_client_simple(testapp):
    api = http.HTTPClient(HOSTS.apitester, token='pippo', logger=testapp.application.logger)

    with testapp.application.app_context():
        res = api.delete('/status/202')
        Asserter.assert_equals(res.status, httpcode.ACCEPTED)
        res = api.patch('/status/400')
        Asserter.assert_equals(res.status, httpcode.BAD_REQUEST)


def test_utils_http_client_exception(testapp):
    logger = testapp.application.logger
    api = http.HTTPClient(HOSTS.apitester, token='pippo', raise_on_exc=True, logger=logger)
    fake_api = http.HTTPClient(HOSTS.fake, username='test', password='test', logger=logger)

    with testapp.application.app_context():
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

    with testapp.application.app_context():
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
    with testapp.application.app_context():
        responses = batch.HTTPBatchRequests(logger=testapp.application.logger).request([
            dict(url=f"{HOSTS.apitester}/anything", method="GET", headers={"HDR1": "HDR1"}),
            dict(url=f"{HOSTS.apitester}/status/{httpcode.NOT_FOUND}", method="GET"),
            dict(url=HOSTS.fake, method='GET'),
        ])
        Asserter.assert_equals(responses[0].body.headers.Hdr1, 'HDR1')
        Asserter.assert_equals(responses[1].status, httpcode.NOT_FOUND)
        Asserter.assert_equals(responses[2].status, httpcode.SERVICE_UNAVAILABLE)


def test_utils_http_jsonrpc_client(testapp):
    params = dict(a=1, b=2)

    with testapp.application.app_context():
        api = http.JsonRPCClient(HOSTS.apitester, "/anything", logger=testapp.application.logger)
        res = api.request('method.test', params=params)

    data = datastruct.ObjectDict(flask.json.loads(res.data))
    Asserter.assert_equals(data.jsonrpc, '2.0')
    Asserter.assert_equals(data.id, api.request_id)
    Asserter.assert_equals(data.params, params)


def test_healthcheck(testapp):
    res = testapp.get(testapp.application.config.HEALTHCHECK_PATH)
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res, httpcode.SERVICE_UNAVAILABLE)
    HttpAsserter.assert_header(res, 'Content-Type', CTS.json_health, is_in=True)
    Asserter.assert_equals(data.status, 'fail')
    Asserter.assert_equals(data.links, {'about': None})
    Asserter.assert_equals(data.checks.health_true.status, 'pass')
    Asserter.assert_equals(data.checks.test_health_false.status, 'fail')
    Asserter.assert_equals(data.checks.sqlalchemy.status, 'fail')
    Asserter.assert_equals(data.checks.mongo.status, 'fail')
    Asserter.assert_equals(data.checks.redis.status, 'fail')


def test_api_jsonrpc_success(testapp):
    call_id = 1
    jsonrpc_version = '2.0'
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "MyJsonRPC.testAction1",
        "params":  None,
        "id":      call_id
    })
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.jsonrpc, jsonrpc_version)
    Asserter.assert_equals(data.id, call_id)
    Asserter.assert_true(data.result.action1)

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "MyJsonRPC.testAction2"
    })
    HttpAsserter.assert_status_code(res, httpcode.NO_CONTENT)


def test_api_jsonrpc_error(testapp):
    call_id = 1
    jsonrpc_version = '2.0'
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "NotFoundMethod",
        "id":      call_id
    })
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.error.code, rpc.RPCMethodNotFound().code)
    Asserter.assert_equals(data.jsonrpc, jsonrpc_version)
    Asserter.assert_equals(data.id, call_id)
    Asserter.assert_true(data.error.message)

    res = testapp.post('/rpc', base_url=base_url, json={})
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.error.code, rpc.RPCParseError().code)

    res = testapp.post('/rpc', base_url=base_url, json={"jsonrpc": jsonrpc_version})
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.error.code, rpc.RPCInvalidRequest().code)

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "MyJsonRPC.testInternalError",
        "id":      call_id
    })
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.error.code, rpc.RPCInternalError().code)


def test_api_jsonrpc_params(testapp):
    call_id = 1
    jsonrpc_version = '2.0'
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME
    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "MyJsonRPC.testInvalidParams",
        "params":  {"param": "testparam"},
        "id":      call_id
    })
    Asserter.assert_not_in('error', res.get_json())

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": jsonrpc_version,
        "method":  "MyJsonRPC.testInvalidParams",
        "params":  {"params": None},
        "id":      call_id
    })
    data = datastruct.ObjectDict(res.get_json())
    HttpAsserter.assert_status_code(res)
    Asserter.assert_equals(data.error.code, rpc.RPCInvalidParams().code)


def test_useragent(testapp):
    res = testapp.get('/useragent')
    HttpAsserter.assert_status_code(res)
    Asserter.assert_allin(res.get_json().keys(), ('browser', 'device', 'os', 'raw'))
    ua_string = """
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) 
        Chrome/70.0.3538.77 Safari/537.36
    """
    res = useragent.UserAgent().parse(ua_string)
    Asserter.assert_equals(res.raw, ua_string)


def test_utils_date_conversion(testapp):
    exc = False
    fmt = "%d %B %Y %I:%M %p"
    iso_date = '2020-12-28T19:53:00'
    not_iso_date = '28 December 2020 07:53 PM'
    invalid_date = 'invalid_date'

    with testapp.application.app_context():
        res = date.from_iso_format(iso_date, fmt, exc=exc)
        Asserter.assert_true(res)
        Asserter.assert_equals(not_iso_date, res)

        res = date.to_iso_format(not_iso_date, fmt, exc=exc)
        Asserter.assert_true(res)
        Asserter.assert_equals(iso_date, res)

        Asserter.assert_none(date.from_iso_format(invalid_date, fmt, exc=exc))
        Asserter.assert_none(date.to_iso_format(invalid_date, fmt, exc=exc))


def test_correlation_id(testapp):
    request_id_header = 'X-Request-ID'
    res = testapp.get('/')
    HttpAsserter.assert_header(res, request_id_header, is_in=True)
    Asserter.assert_type(res.headers[request_id_header], str)

    req_id = uuid.get_uuid()
    res = testapp.get('/', headers={request_id_header: req_id})
    HttpAsserter.assert_header(res, request_id_header, req_id)

    req_id = 'invalid_req_id'
    res = testapp.get('/', headers={request_id_header: req_id})
    Asserter.assert_different(res.headers[request_id_header], req_id)
