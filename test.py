import pytest

from flask import json, Response as Resp
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
    assert res.headers['Content-Type'] == 'application/json'


def test_api_cors(client, app):
    res = client.get('/', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.headers['Access-Control-Allow-Origin'] == '*'


def test_dispatch_error_web(client):
    res = client.get('/web-page-not-found')
    assert res.status_code == 404 and 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client, app):
    res = client.get('/api-not-found', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == 404 and res.headers['Content-Type'] == 'application/json'
