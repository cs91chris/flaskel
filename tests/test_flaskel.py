import os
import werkzeug.exceptions

from flaskel import httpcode
from flaskel.utils import uuid, http
# noinspection PyUnresolvedReferences
from . import app_prod, app_dev, testapp


def test_app_dev(app_dev):
    client = app_dev.test_client()
    assert app_dev.config['FLASK_ENV'] == 'development'
    assert app_dev.config['SECRET_KEY'] == 'very_complex_string'

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
    assert 'application/json' in res.headers['Content-Type']


def test_api_cors(testapp):
    res = testapp.get('/', base_url='http://api.' + testapp.application.config['SERVER_NAME'])
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

    res_query_string = testapp.post(
        '/method_override?_method_override=PUT'
    )
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
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with testapp.application.app_context():
        res = api.delete('/status/200')
        assert res['status'] == httpcode.SUCCESS
        res = api.patch('/status/400')
        assert res['status'] == httpcode.BAD_REQUEST


def test_utils_http_client_exception(testapp):
    api = http.HTTPClient("http://httpbin.org", token='pippo')
    fake_api = http.HTTPClient('localhost', username='test', password='test')

    with testapp.application.app_context():
        res = fake_api.put('/', timeout=0.1)
        assert res['status'] == httpcode.SERVICE_UNAVAILABLE

        try:
            api.request('/status/500', 'PUT', raise_on_exc=True)
        except http.client.http_exc.HTTPError as exc:
            assert exc.response.status_code == httpcode.INTERNAL_SERVER_ERROR

        try:
            fake_api.request('/', raise_on_exc=True, timeout=0.1)
        except werkzeug.exceptions.HTTPException as exc:
            assert exc.code == httpcode.INTERNAL_SERVER_ERROR


def test_utils_http_client_filename(testapp):
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with testapp.application.app_context():
        filename = "pippo.txt"
        api.get('/response-headers', params={
            'Content-Disposition': "attachment; filename={}".format(filename)
        })
        assert api.get_response_filename() == filename

        api.post('/response-headers', params={
            'Content-Disposition': "filename={}".format(filename)
        })
        assert api.get_response_filename() == filename

        api.post('/response-headers', params={
            'Content-Disposition': filename
        })
        assert api.get_response_filename() is None
