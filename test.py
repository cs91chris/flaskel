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


def test_app_runs(client, app):
    base_url = 'http://api.' + app.config['SERVER_NAME']
    res = client.get('/', base_url=base_url)
    assert res.status_code == 200


def test_app_returns_json(client, app):
    base_url = 'http://api.' + app.config['SERVER_NAME']
    res = client.get('/', base_url=base_url)
    assert res.headers['Content-Type'] == 'application/json'


def test_app_return_html(client):
    res = client.get('/')
    assert res.status_code == 200 and 'text/html' in res.headers['Content-Type']

