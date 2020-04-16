import werkzeug.exceptions
from flask import jsonify, request

from flaskel.utils import uuid, http
from flaskel import httpcode
# noinspection PyUnresolvedReferences
from . import app, client


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == httpcode.SUCCESS


def test_app_return_html(client):
    res = client.get('/web')
    assert 'text/html' in res.headers['Content-Type']


def test_app_returns_json(client, app):
    res = client.get('/', base_url='http://api.' + app.config['SERVER_NAME'])
    assert 'application/json' in res.headers['Content-Type']


def test_api_cors(client, app):
    res = client.get('/', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.headers['Access-Control-Allow-Origin'] == '*'


def test_dispatch_error_web(client):
    res = client.get('/web-page-not-found')
    assert res.status_code == httpcode.NOT_FOUND
    assert 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client, app):
    res = client.get('/api-not-found', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == httpcode.NOT_FOUND
    assert 'application/json' in res.headers['Content-Type']


def test_method_override(client, app):
    @app.route('/method_override', methods=['POST', 'PUT'])
    def method_override_post():
        return '', httpcode.SUCCESS if request.method == 'PUT' else httpcode.METHOD_NOT_ALLOWED

    res_header = client.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    assert res_header.status_code == httpcode.SUCCESS

    res_query_string = client.post(
        '/method_override?_method_override=PUT'
    )
    assert res_query_string.status_code == httpcode.SUCCESS


def test_converters(client, app):
    @app.route("/list/<list('-'):data>")
    def list_converter(data):
        return jsonify(data)

    res = client.get('/list/a-b-c')
    assert res.status_code == httpcode.SUCCESS
    assert len(res.get_json()) == 3


def test_utils_get_json(client, app):
    @app.route('/json', methods=['POST'])
    def get_invalid_json():
        http.get_json()
        return '', httpcode.SUCCESS

    res = client.post('/json')
    assert res.status_code == httpcode.BAD_REQUEST


def test_utils_send_file(client, app):
    @app.route('/download')
    def download():
        return http.send_file('./', request.args.get('filename'))

    res = client.get('/download?filename=requirements.txt')

    assert res.data == b''
    assert res.status_code == httpcode.SUCCESS
    assert res.headers.get('Content-Disposition') == 'attachment; filename=requirements.txt'
    assert res.headers.get('X-Sendfile').endswith('./requirements.txt')
    assert res.headers.get('X-Accel-Redirect') == './requirements.txt'

    res = client.get('/download?filename=nofile.txt')
    assert res.status_code == httpcode.NOT_FOUND


def test_utils_uuid(client, app):
    @app.route('/uuid')
    def return_uuid():
        return jsonify(dict(
            uuid1=uuid.get_uuid(ver=1),
            uuid3=uuid.get_uuid(ver=3),
            uuid4=uuid.get_uuid(),
            uuid5=uuid.get_uuid(ver=5),
        ))

    res = client.get('/uuid')
    data = res.get_json()
    assert uuid.check_uuid('fake uuid') is False
    assert uuid.check_uuid(data.get('uuid1'), ver=1) is True
    assert uuid.check_uuid(data.get('uuid3'), ver=3) is True
    assert uuid.check_uuid(data.get('uuid4')) is True
    assert uuid.check_uuid(data.get('uuid5'), ver=5) is True


def test_crypto(client, app):
    passwd = 'my-favourite-password'
    crypto = app.extensions['argon2']

    @app.route('/crypt')
    def crypt():
        return crypto.generate_hash(passwd)

    res = client.get('/crypt')
    assert crypto.verify_hash(res.data, passwd)
    assert crypto.verify_hash(res.data, "wrong-pass") is False


def test_utils_http_client(app):
    from flaskel.utils import http

    api = http.HTTPClient("http://httpbin.org", token='pippo')
    fake_api = http.HTTPClient('localhost', username='test', password='test')

    with app.app_context():
        res = api.delete('/status/200')
        assert res['status'] == httpcode.SUCCESS
        res = api.patch('/status/400')
        assert res['status'] == httpcode.BAD_REQUEST

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
