import os
import werkzeug.exceptions

from flaskel import httpcode
from flaskel.utils import uuid, http
# noinspection PyUnresolvedReferences
from . import app, client


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == httpcode.SUCCESS


def test_app_return_html(client):
    res = client.get('/web')
    assert 'text/html' in res.headers['Content-Type']


def test_app_returns_json(client):
    res = client.get('/', base_url='http://api.' + client.application.config['SERVER_NAME'])
    assert 'application/json' in res.headers['Content-Type']


def test_api_cors(client):
    res = client.get('/', base_url='http://api.' + client.application.config['SERVER_NAME'])
    assert res.headers['Access-Control-Allow-Origin'] == '*'


def test_dispatch_error_web(client):
    res = client.get('/web-page-not-found')
    assert res.status_code == httpcode.NOT_FOUND
    assert 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client):
    res = client.get('/api-not-found', base_url='http://api.' + client.application.config['SERVER_NAME'])
    assert res.status_code == httpcode.NOT_FOUND
    assert 'application/json' in res.headers['Content-Type']


def test_force_https(app):
    _app = app('production')

    res = _app.test_client().get('/test_https')
    assert res.status_code == httpcode.SUCCESS
    assert res.data == b'https'


def test_reverse_proxy(app):
    _app = app('production')

    res = _app.test_client().get('/proxy', headers={
        'X-Script-Name': '/test'
    })
    data = res.get_json()

    assert res.status_code == httpcode.SUCCESS
    assert data['script_name'] == '/test'
    assert data['path_info'] == '/proxy'


def test_secret_key_prod(app):
    client.application = app('production')
    assert client.application.config['FLASK_ENV'] == 'production'
    assert os.path.isfile('.secret.key')
    os.remove('.secret.key')


def test_secret_key_dev(client):
    assert client.application.config['SECRET_KEY'] == 'very_complex_string'


def test_method_override(client):
    res_header = client.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    assert res_header.status_code == httpcode.SUCCESS

    res_query_string = client.post(
        '/method_override?_method_override=PUT'
    )
    assert res_query_string.status_code == httpcode.SUCCESS


def test_converters(client):
    res = client.get('/list/a-b-c')
    assert res.status_code == httpcode.SUCCESS
    assert len(res.get_json()) == 3


def test_utils_get_json(client):
    res = client.post('/invalid-json')
    assert res.status_code == httpcode.BAD_REQUEST


def test_utils_send_file(client):
    res = client.get('/download?filename=MANIFEST.in')

    assert res.status_code == httpcode.SUCCESS
    assert res.headers.get('Content-Disposition') == 'attachment; filename=MANIFEST.in'
    assert res.headers.get('X-Sendfile').endswith('./MANIFEST.in')
    assert res.headers.get('X-Accel-Redirect') == './MANIFEST.in'
    assert res.data == b''

    res = client.get('/download?filename=nofile.txt')
    assert res.status_code == httpcode.NOT_FOUND


def test_utils_uuid(client):
    res = client.get('/uuid')
    data = res.get_json()
    assert uuid.check_uuid('fake uuid') is False
    assert uuid.check_uuid(data.get('uuid1'), ver=1) is True
    assert uuid.check_uuid(data.get('uuid3'), ver=3) is True
    assert uuid.check_uuid(data.get('uuid4')) is True
    assert uuid.check_uuid(data.get('uuid5'), ver=5) is True


def test_crypto(client):
    passwd = 'my-favourite-password'
    crypto = client.application.extensions['argon2']

    res = client.get('/crypt/{}'.format(passwd))
    assert crypto.verify_hash(res.data, passwd)
    assert crypto.verify_hash(res.data, "wrong-pass") is False


def test_utils_http_client_simple(client):
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with client.application.app_context():
        res = api.delete('/status/200')
        assert res['status'] == httpcode.SUCCESS
        res = api.patch('/status/400')
        assert res['status'] == httpcode.BAD_REQUEST


def test_utils_http_client_exception(client):
    api = http.HTTPClient("http://httpbin.org", token='pippo')
    fake_api = http.HTTPClient('localhost', username='test', password='test')

    with client.application.app_context():
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


def test_utils_http_client_filename(client):
    api = http.HTTPClient("http://httpbin.org", token='pippo')

    with client.application.app_context():
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
