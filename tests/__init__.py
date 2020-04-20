import pytest
from flask.testing import FlaskClient
from flask_errors_handler import SubdomainDispatcher

from flaskel import bootstrap
from flaskel.ext import EXTENSIONS
from .blueprints import BLUEPRINTS
from flaskel.patch import ReverseProxied, HTTPMethodOverride, ForceHttps


@pytest.fixture
def app_prod():
    """

    """
    class TestClient(FlaskClient):
        """
            Implement this to customize Flask client
            Form example:
                    def fetch(self, url, *args, **kwargs):
                        return self.open(url, method='FETCH', *args, **kwargs)
        """

    _app = bootstrap(
        conf_map=dict(FLASK_ENV='production'),
        blueprints=BLUEPRINTS + (None,) + ((None,),),  # NB: needed to complete coverage
        extensions=EXTENSIONS + (None,) + ((None,),),  # NB: needed to complete coverage
        jinja_fs_loader=["skeleton/templates"],
        static_folder="skeleton/static"
    )

    _app.wsgi_app = ForceHttps(_app.wsgi_app)
    _app.wsgi_app = ReverseProxied(_app.wsgi_app)
    _app.wsgi_app = HTTPMethodOverride(_app.wsgi_app)

    error = _app.extensions['errors_handler']
    error.register_dispatcher(SubdomainDispatcher)

    _app.test_client_class = TestClient
    _app.testing = True

    return _app


@pytest.fixture
def app_dev():
    """

    """
    _app = bootstrap(
        blueprints=BLUEPRINTS,
        extensions=EXTENSIONS,
        template_folder="skeleton/templates",
        static_folder="skeleton/static"
    )
    _app.testing = True
    return _app


@pytest.fixture
def testapp(app_prod):
    """

    :param app_prod:
    :return:
    """
    return app_prod.test_client()
