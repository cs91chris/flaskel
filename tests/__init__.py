import pytest
from flask.testing import FlaskClient
from flask_response_builder import encoders
from flask_errors_handler import SubdomainDispatcher

from flaskel import bootstrap
from flaskel.ext import EXTENSIONS
from skeleton.blueprints import BLUEPRINTS
from flaskel.patch import ReverseProxied, HTTPMethodOverride


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

    _app = bootstrap(
        blueprints=BLUEPRINTS + (None,) + ((None,),),  # NB: needed to complete coverage
        extensions=EXTENSIONS + (None,) + ((None,),),  # NB: needed to complete coverage
        jinja_fs_loader=["skeleton/templates"],
        static_folder="skeleton/static"
    )
    _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    error = _app.extensions['errors_handler']
    error.register_dispatcher(SubdomainDispatcher)

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
