import flask
from flask.testing import FlaskClient

from flaskel.builder import AppBuilder


class TestClient(FlaskClient):
    def fetch(self, url, *args, **kwargs):  # pragma: no cover
        return self.open(url, method='FETCH', *args, **kwargs)

    @classmethod
    def get_app(cls, conf, **kwargs):
        """

        :param conf:
        :param kwargs:
        :return:
        """
        app = AppBuilder(**kwargs).get_or_create(conf)
        app.test_client_class = cls
        app.TESTING = True

        if not flask.has_app_context():
            app.app_context().push()

        return app

    def jsonrpc(self, url, method=None, call_id=None, params=None, version="2.0", **kwargs):
        """

        :param url:
        :param method:
        :param call_id:
        :param params:
        :param version:
        :param kwargs:
        :return:
        """
        payload = {
            "jsonrpc": version,
            "method":  method,
            "params":  params
        }
        if call_id:
            payload['id'] = call_id

        kwargs.setdefault('json', payload)
        return self.post(url, **kwargs)
