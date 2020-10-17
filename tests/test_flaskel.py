import os

import werkzeug.exceptions

from flaskel import httpcode
from flaskel.utils import http, uuid
from flaskel.utils.http.rpc import RPCInvalidRequest, RPCMethodNotFound, RPCParseError
# noinspection PyUnresolvedReferences
from tests import app_dev, app_prod, testapp


def test_app_dev(app_dev):
    client = app_dev.test_client()
    assert app_dev.config['FLASK_ENV'] == 'development'
    assert app_dev.config['SECRET_KEY'] == 'fake_very_complex_string'

    res = client.get('/')
    assert res.status_code == httpcode.SUCCESS

    res = client.get('/test_https', base_url='http://' + app_dev.config['SERVER_NAME'])
    assert res.status_code == httpcode.SUCCESS
    data = res.get_json()

    assert data['scheme'] == 'http'
    assert data['url_for'].startswith('http')


def test_app_runs(testapp):
    res = testapp.get('/')
    assert res.status_code == httpcode.SUCCESS


def test_app_return_html(testapp):
    res = testapp.get('/web')
    assert 'text/html' in res.headers['Content-Type']


def test_app_returns_json(testapp):
    res = testapp.get('/', base_url='http://api.' + testapp.application.config['SERVER_NAME'])
    assert res.status_code == httpcode.NOT_FOUND
    assert 'application/problem+json' in res.headers['Content-Type']


def test_api_resources(testapp):
    base_url = 'http://api.' + testapp.application.config['SERVER_NAME']

    res = testapp.get('/resources', base_url=base_url, headers={'Accept': 'application/xml'})
    assert res.status_code == httpcode.SUCCESS
    assert 'application/xml' in res.headers['Content-Type']

    res = testapp.get('/resources/1', base_url=base_url)
    assert res.status_code == httpcode.SUCCESS
    assert 'application/json' in res.headers['Content-Type']

    res = testapp.get('/resources/1/items', base_url=base_url)
    assert res.status_code == httpcode.SUCCESS
    assert 'application/json' in res.headers['Content-Type']

    res = testapp.get('/resources/1/not-found', base_url=base_url)
    assert res.status_code == httpcode.NOT_FOUND
    assert 'application/problem+json' in res.headers['Content-Type']

    res = testapp.delete('/resources/1', base_url=base_url)
    assert res.status_code == httpcode.NO_CONTENT

    data = {'item': 'test'}
    res = testapp.put('/resources/1', json=data, base_url=base_url)
    assert res.status_code == httpcode.SUCCESS

    res = testapp.post('/resources', json=data, base_url=base_url)
    assert res.status_code == httpcode.CREATED

    res = testapp.post('/resources/1/items', json=data, base_url=base_url)
    assert res.status_code == httpcode.CREATED


def test_api_cors(testapp):
    res = testapp.get('/resources', base_url='http://api.' + testapp.application.config['SERVER_NAME'])
    assert res.headers['Access-Control-Allow-Origin'] == '*'


def test_dispatch_error_web(testapp):
    res = testapp.get('/web-page-not-found')
    assert res.status_code == httpcode.NOT_FOUND
    assert 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(testapp):
    res = testapp.get('/api-not-found', base_url='http://api.' + testapp.application.config['SERVER_NAME'])
    assert res.status_code == httpcode.NOT_FOUND
    assert res.headers['Content-Type'] == 'application/problem+json'


def test_force_https(testapp):
    res = testapp.get('/test_https', base_url='http://' + testapp.application.config['SERVER_NAME'])
    assert res.status_code == httpcode.SUCCESS
    data = res.get_json()

    assert data['scheme'] == 'https'
    assert data['url_for'].startswith('https')


def test_reverse_proxy(testapp):
    res = testapp.get('/proxy', headers={
        'X-Forwarded-Prefix': '/test'
    })
    data = res.get_json()

    assert res.status_code == httpcode.SUCCESS
    assert data['script_name'] == '/test'
    assert data['original']['SCRIPT_NAME'] == ''


def test_secret_key_prod(testapp):
    assert testapp.application.config['FLASK_ENV'] == 'production'
    assert os.path.isfile('.secret.key')
    os.remove('.secret.key')


def test_method_override(testapp):
    res_header = testapp.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    assert res_header.status_code == httpcode.SUCCESS

    res_query_string = testapp.post('/method_override?_method_override=PUT')
    assert res_query_string.status_code == httpcode.SUCCESS


def test_converters(testapp):
    res = testapp.get('/list/a-b-c')
    assert res.status_code == httpcode.SUCCESS
    assert len(res.get_json()) == 3


def test_utils_get_json(testapp):
    res = testapp.post('/invalid-json')
    assert res.status_code == httpcode.BAD_REQUEST


def test_utils_send_file(testapp):
    res = testapp.get('/download?filename=MANIFEST.in')

    assert res.status_code == httpcode.SUCCESS
    assert res.headers.get('Content-Disposition') == 'attachment; filename=MANIFEST.in'
    assert res.headers.get('X-Sendfile').endswith('./MANIFEST.in')
    assert res.headers.get('X-Accel-Redirect') == './MANIFEST.in'
    assert res.data == b''

    res = testapp.get('/download?filename=nofile.txt')
    assert res.status_code == httpcode.NOT_FOUND


def test_utils_uuid(testapp):
    res = testapp.get('/uuid')
    data = res.get_json()
    assert uuid.check_uuid('fake uuid') is False
    assert uuid.check_uuid(data.get('uuid1'), ver=1) is True
    assert uuid.check_uuid(data.get('uuid3'), ver=3) is True
    assert uuid.check_uuid(data.get('uuid4')) is True
    assert uuid.check_uuid(data.get('uuid5'), ver=5) is True


def test_crypto(testapp):
    passwd = 'my-favourite-password'
    crypto = testapp.application.extensions['argon2']

    res = testapp.get('/crypt/{}'.format(passwd))
    assert crypto.verify_hash(res.data, passwd)
    assert crypto.verify_hash(res.data, "wrong-pass") is False


def test_utils_http_client_simple(testapp):
    api = http.HTTPClient("http://httpbin.org", token='pippo', logger=testapp.application.logger)

    with testapp.application.app_context():
        res = api.delete('/status/200')
        assert res['status'] == httpcode.SUCCESS
        res = api.patch('/status/400')
        assert res['status'] == httpcode.BAD_REQUEST


def test_utils_http_client_exception(testapp):
    api = http.HTTPClient("http://httpbin.org", token='pippo', raise_on_exc=True)
    fake_api = http.HTTPClient('localhost', username='test', password='test')

    with testapp.application.app_context():
        res = fake_api.put('/', timeout=0.1)
        assert res['status'] == httpcode.SERVICE_UNAVAILABLE

        try:
            api.request('/status/500', 'PUT')
        except http.client.http_exc.HTTPError as exc:
            assert exc.response.status_code == httpcode.INTERNAL_SERVER_ERROR

        try:
            fake_api.request('/', timeout=0.1)
        except werkzeug.exceptions.HTTPException as exc:
            assert exc.code == httpcode.INTERNAL_SERVER_ERROR


def test_utils_http_client_filename(testapp):
    from flaskel.utils import http
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with testapp.application.app_context():
        filename = "pippo.txt"
        res = api.get('/response-headers', params={
            'Content-Disposition': "attachment; filename={}".format(filename)
        })
        assert http.misc.get_response_filename(res['headers']) == filename

        res = api.post('/response-headers', params={
            'Content-Disposition': "filename={}".format(filename)
        })
        assert http.misc.get_response_filename(res['headers']) == filename

        res = api.post('/response-headers', params={
            'Content-Disposition': filename
        })
        assert http.misc.get_response_filename(res['headers']) is None


def test_utils_http_jsonrpc_client(testapp):
    from flask import json

    params = dict(a=1, b=2)

    with testapp.application.app_context():
        api = http.JsonRPCClient("http://httpbin.org", "/anything")
        res = api.request('method.test', params=params)

    data = json.loads(res['data'])
    assert data['jsonrpc'] == '2.0'
    assert data['id'] == api.request_id
    assert data['params'] == params


def test_healthcheck(testapp):
    res = testapp.get('/healthcheck')
    data = res.get_json()

    assert res.status_code == httpcode.SERVICE_UNAVAILABLE
    assert res.headers['Content-Type'] == 'application/health+json'
    assert data['status'] == 'fail'
    assert data['links'] == {'about': None}
    assert data['checks']['health_true']['status'] == 'pass'
    assert data['checks']['test_health_false']['status'] == 'fail'
    assert data['checks']['sqlalchemy']['status'] == 'fail'
    assert data['checks']['mongo']['status'] == 'fail'
    assert data['checks']['redis']['status'] == 'fail'


def test_api_jsonrpc_ok(testapp):
    call_id = 1
    base_url = 'http://api.' + testapp.application.config['SERVER_NAME']

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "MyJsonRPC.testAction1",
        "params":  None,
        "id":      call_id
    })

    data = res.get_json()
    assert res.status_code == 200
    assert data['jsonrpc'] == "2.0"
    assert data['id'] == call_id
    assert data['result']['action1'] is True

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "MyJsonRPC.testAction2"
    })
    assert res.status_code == 204


def test_api_jsonrpc_error(testapp):
    call_id = 1
    base_url = 'http://api.' + testapp.application.config['SERVER_NAME']

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "NotFoundMethod",
        "id":      call_id
    })

    data = res.get_json()
    assert res.status_code == 200
    assert data['error']['code'] == RPCMethodNotFound().code
    assert data['jsonrpc'] == "2.0"
    assert data['id'] == call_id
    assert len(data['error']['message']) > 0

    res = testapp.post('/rpc', base_url=base_url, json={})
    data = res.get_json()
    assert res.status_code == 200
    assert data['error']['code'] == RPCParseError().code

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0"
    })
    data = res.get_json()
    assert res.status_code == 200
    assert data['error']['code'] == RPCInvalidRequest().code


def test_useragent(testapp):
    res = testapp.get('/useragent')
    data = res.get_json()

    assert res.status_code == httpcode.SUCCESS
    all(i in data.keys() for i in (
        'browser', 'device', 'os', 'raw'
    ))
