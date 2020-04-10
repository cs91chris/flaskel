import pytest
from flask import jsonify, request
from flask.testing import FlaskClient

from flaskel import utils
from app import create_app


@pytest.fixture
def app():
    """

    :return:
    """
    class TestClient(FlaskClient):
        """
            Implement this to customize Flask client
            Form example:
                    def fetch(self, url, *args, **kwargs):
                        return self.open(url, method='FETCH', *args, **kwargs)
        """
        pass

    _app = create_app(template_folder='templates', static_folder='static')
    _app.test_client_class = TestClient
    _app.testing = True
    return _app


@pytest.fixture
def client(app):
    """

    :param app:
    :return:
    """
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == 404


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
    assert res.status_code == 404
    assert 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client, app):
    res = client.get('/api-not-found', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == 404
    assert 'application/json' in res.headers['Content-Type']


def test_method_override_header(client, app):
    @app.route('/method_override', methods=['POST', 'PUT'])
    def method_override_post():
        return '', 200 if request.method == 'PUT' else 405

    res_header = client.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    assert res_header.status_code == 200

    res_query_string = client.post(
        '/method_override?_method_override=PUT'
    )
    assert res_query_string.status_code == 200


def test_converters(client, app):
    @app.route("/list/<list('-'):data>")
    def list_converter(data):
        return jsonify(data)

    res = client.get('/list/a-b-c')
    assert res.status_code == 200
    assert len(res.get_json()) == 3


def test_utils_get_json(client, app):
    @app.route('/json', methods=['POST'])
    def get_invalid_json():
        utils.get_json()
        return '', 200

    res = client.post('/json')
    assert res.status_code == 400


def test_utils_uuid(client, app):
    @app.route('/uuid')
    def return_uuid():
        return jsonify(dict(uuid=utils.get_uuid()))

    res = client.get('/uuid')
    data = res.get_json()
    assert utils.check_uuid('fake uuid') is False
    assert utils.check_uuid(data.get('uuid')) is True
