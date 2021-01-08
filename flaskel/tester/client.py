from flask.testing import FlaskClient

from flaskel.builder import AppBuilder


class TestClient(FlaskClient):
    def fetch(self, url, *args, **kwargs):
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
        return app
