import os

import flask
import werkzeug.exceptions

from flaskel import http, httpcode
from flaskel.http.batch import HTTPBatchRequests
from flaskel.http.rpc import RPCInvalidRequest, RPCMethodNotFound, RPCParseError
from flaskel.tester.mixins import Asserter
from flaskel.utils import datastuct, uuid
# noinspection PyUnresolvedReferences
from tests import app_dev, app_prod, testapp


def test_app_dev(app_dev):
    client = app_dev.test_client()
    Asserter.assert_equals(app_dev.config.FLASK_ENV, 'development')
    Asserter.assert_equals(app_dev.config.SECRET_KEY, 'fake_very_complex_string')

    res = client.get('/')
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)

    res = client.get('/test_https', base_url='http://' + app_dev.config.SERVER_NAME)
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(data.scheme, 'http')
    Asserter.assert_true(data.url_for.startswith('http'))


def test_app_runs(testapp):
    res = testapp.get('/')
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)


def test_app_return_html(testapp):
    res = testapp.get('/web')
    Asserter.assert_in('text/html', res.headers['Content-Type'])


def test_app_returns_json(testapp):
    res = testapp.get('/', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    Asserter.assert_equals(res.status_code, httpcode.NOT_FOUND)
    Asserter.assert_in('application/problem+json', res.headers['Content-Type'])


def test_api_resources(testapp):
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.get('/resources', base_url=base_url, headers={'Accept': 'application/xml'})
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_in('application/xml', res.headers['Content-Type'])

    res = testapp.get('/resources/1', base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_in('application/json', res.headers['Content-Type'])

    res = testapp.get('/resources/1/items', base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_in('application/json', res.headers['Content-Type'])

    res = testapp.get('/resources/1/not-found', base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.NOT_FOUND)
    Asserter.assert_in('application/problem+json', res.headers['Content-Type'])

    res = testapp.delete('/resources/1', base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.NO_CONTENT)

    data = {'item': 'test'}
    res = testapp.put('/resources/1', json=data, base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)

    res = testapp.post('/resources', json=data, base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.CREATED)

    res = testapp.post('/resources/1/items', json=data, base_url=base_url)
    Asserter.assert_equals(res.status_code, httpcode.CREATED)


def test_api_cors(testapp):
    res = testapp.get('/resources', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    Asserter.assert_equals(res.headers['Access-Control-Allow-Origin'], '*')


def test_dispatch_error_web(testapp):
    res = testapp.get('/web-page-not-found')
    Asserter.assert_equals(res.status_code, httpcode.NOT_FOUND)
    Asserter.assert_in('text/html', res.headers['Content-Type'])


def test_dispatch_error_api(testapp):
    res = testapp.get('/api-not-found', base_url='http://api.' + testapp.application.config.SERVER_NAME)
    Asserter.assert_equals(res.status_code, httpcode.NOT_FOUND)
    Asserter.assert_in('application/problem+json', res.headers['Content-Type'])


def test_force_https(testapp):
    res = testapp.get('/test_https', base_url='http://' + testapp.application.config.SERVER_NAME)
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(data.scheme, 'https')
    Asserter.assert_true(data.url_for.startswith('https'))


def test_reverse_proxy(testapp):
    res = testapp.get('/proxy', headers={
        'X-Forwarded-Prefix': '/test'
    })
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
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
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)

    res = testapp.post('/method_override?_method_override=PUT')
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)


def test_converters(testapp):
    res = testapp.get('/list/a-b-c')
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_equals(len(res.get_json()), 3)


def test_utils_get_json(testapp):
    res = testapp.post('/invalid-json')
    Asserter.assert_equals(res.status_code, httpcode.BAD_REQUEST)


def test_utils_send_file(testapp):
    filename = 'MANIFEST.in'
    res = testapp.get(f'/download?filename={filename}')
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_true(res.headers.get('X-Sendfile').endswith(f'./{filename}'))
    Asserter.assert_equals(res.headers.get('Content-Disposition'), f'attachment; filename={filename}')
    Asserter.assert_equals(res.headers.get('X-Accel-Redirect'), f'./{filename}')
    Asserter.assert_equals(res.data, b'')

    res = testapp.get('/download?filename=nofile.txt')
    Asserter.assert_equals(res.status_code, httpcode.NOT_FOUND)


def test_utils_uuid(testapp):
    res = testapp.get('/uuid')
    data = res.get_json()
    Asserter.assert_false(uuid.check_uuid('fake uuid'))
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
    api = http.HTTPClient("http://httpbin.org", token='pippo', logger=testapp.application.logger)

    with testapp.application.app_context():
        res = api.delete('/status/200')
        Asserter.assert_equals(res.status, httpcode.SUCCESS)
        res = api.patch('/status/400')
        Asserter.assert_equals(res.status, httpcode.BAD_REQUEST)


def test_utils_http_client_exception(testapp):
    api = http.HTTPClient("http://httpbin.org", token='pippo', raise_on_exc=True)
    fake_api = http.HTTPClient('http://localhost', username='test', password='test')

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
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with testapp.application.app_context():
        filename = "pippo.txt"
        res = api.get('/response-headers', params={
            'Content-Disposition': f"attachment; filename={filename}"
        })
        Asserter.assert_equals(api.response_filename(res.headers), filename)

        res = api.post('/response-headers', params={
            'Content-Disposition': f"filename={filename}"
        })
        Asserter.assert_equals(api.response_filename(res.headers), filename)

        res = api.post('/response-headers', params={
            'Content-Disposition': filename
        })
        Asserter.assert_none(api.response_filename(res.headers))


def test_http_client_batch():
    responses = HTTPBatchRequests().request([
        dict(url="http://httpbin.org/anything", method="GET", headers={"HDR1": "HDR1"}),
        dict(url=f"http://httpbin.org/status/{httpcode.NOT_FOUND}", method="GET"),
        dict(url="http://not_exists_domain.com", method='GET'),
    ])
    Asserter.assert_equals(responses[0].body.headers.Hdr1, 'HDR1')
    Asserter.assert_equals(responses[1].status, httpcode.NOT_FOUND)
    Asserter.assert_equals(responses[2].status, httpcode.SERVICE_UNAVAILABLE)


def test_utils_http_jsonrpc_client(testapp):
    params = dict(a=1, b=2)

    with testapp.application.app_context():
        api = http.JsonRPCClient("http://httpbin.org", "/anything")
        res = api.request('method.test', params=params)

    data = datastuct.ObjectDict(flask.json.loads(res.data))
    Asserter.assert_equals(data.jsonrpc, '2.0')
    Asserter.assert_equals(data.id, api.request_id)
    Asserter.assert_equals(data.params, params)


def test_healthcheck(testapp):
    res = testapp.get('/healthcheck')
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SERVICE_UNAVAILABLE)
    Asserter.assert_equals(res.headers['Content-Type'], 'application/health+json')
    Asserter.assert_equals(data.status, 'fail')
    Asserter.assert_equals(data.links, {'about': None})
    Asserter.assert_equals(data.checks.health_true.status, 'pass')
    Asserter.assert_equals(data.checks.test_health_false.status, 'fail')
    Asserter.assert_equals(data.checks.sqlalchemy.status, 'fail')
    Asserter.assert_equals(data.checks.mongo.status, 'fail')
    Asserter.assert_equals(data.checks.redis.status, 'fail')


def test_api_jsonrpc_success(testapp):
    call_id = 1
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "MyJsonRPC.testAction1",
        "params":  None,
        "id":      call_id
    })
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_equals(data.jsonrpc, "2.0")
    Asserter.assert_equals(data.id, call_id)
    Asserter.assert_true(data.result.action1)

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "MyJsonRPC.testAction2"
    })
    Asserter.assert_equals(res.status_code, httpcode.NO_CONTENT)


def test_api_jsonrpc_error(testapp):
    call_id = 1
    base_url = 'http://api.' + testapp.application.config.SERVER_NAME

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0",
        "method":  "NotFoundMethod",
        "id":      call_id
    })
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_equals(data.error.code, RPCMethodNotFound().code)
    Asserter.assert_equals(data.jsonrpc, "2.0")
    Asserter.assert_equals(data.id, call_id)
    Asserter.assert_greater(len(data.error.message), 0)

    res = testapp.post('/rpc', base_url=base_url, json={})
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_equals(data.error.code, RPCParseError().code)

    res = testapp.post('/rpc', base_url=base_url, json={
        "jsonrpc": "2.0"
    })
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_equals(data.error.code, RPCInvalidRequest().code)


def test_useragent(testapp):
    res = testapp.get('/useragent')
    data = datastuct.ObjectDict(res.get_json())
    Asserter.assert_equals(res.status_code, httpcode.SUCCESS)
    Asserter.assert_allin(data.keys(), (
        'browser', 'device', 'os', 'raw'
    ))
