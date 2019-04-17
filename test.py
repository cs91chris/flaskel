import pytest

from flask import json
from flask import request
from flask import Response as Resp

from flask.testing import FlaskClient
from werkzeug.utils import cached_property

from app import create_app


@pytest.fixture
def app():
    class Response(Resp):
        @cached_property
        def json(self):
            return json.loads(self.data)

    class TestClient(FlaskClient):
        def open(self, *args, **kwargs):
            if 'json' in kwargs:
                kwargs['data'] = json.dumps(kwargs.pop('json'))
                kwargs['Content-Type'] = 'application/json'
            return super(TestClient, self).open(*args, **kwargs)

    _app = create_app()
    _app.response_class = Response
    _app.test_client_class = TestClient
    _app.testing = True

    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get('/web')
    assert res.status_code == 200


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
    assert res.status_code == 404 and 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client, app):
    res = client.get('/api-not-found', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == 404 and 'application/json' in res.headers['Content-Type']


def test_method_override_header(client, app):
    @app.route('/method_override', methods=['POST', 'PUT'])
    def method_override_post():
        return '', 200 if request.method == 'PUT' else 405

    res_header = client.post(
        '/method_override',
        headers={'X-HTTP-Method-Override': 'PUT'}
    )
    res_query_string = client.post(
        '/method_override?_method_override=PUT'
    )
    assert res_header.status_code == 200 and res_query_string.status_code == 200
