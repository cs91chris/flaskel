import pytest
from flask.testing import FlaskClient

from .blueprints import BLUEPRINTS
from flaskel.ext import EXTENSIONS
from flaskel.patch import ForceHttps
from flaskel import default_app_factory


class TestClient(FlaskClient):
    """
        Implement this to customize Flask client
        Form example:
                def fetch(self, url, *args, **kwargs):
                    return self.open(url, method='FETCH', *args, **kwargs)
    """


@pytest.fixture
def app_prod():
    """

    """
    _app = default_app_factory(
        conf_map=dict(FLASK_ENV='production'),
        blueprints=BLUEPRINTS + (None,) + ((None,),),  # NB: needed to complete coverage
        extensions=EXTENSIONS + (None,) + ((None,),),  # NB: needed to complete coverage
        jinja_fs_loader=["skeleton/templates"],
        static_folder="skeleton/static"
    )

    _app.wsgi_app = ForceHttps(_app.wsgi_app)
    _app.test_client_class = TestClient
    _app.testing = True
    return _app


@pytest.fixture
def app_dev():
    """

    """
    _app = default_app_factory(
        blueprints=BLUEPRINTS,
        extensions=EXTENSIONS,
        template_folder="skeleton/templates",
        static_folder="skeleton/static"
    )

    _app.test_client_class = TestClient
    _app.testing = True
    return _app


@pytest.fixture
def testapp(app_prod):
    """

    :param app_prod:
    :return:
    """
    return app_prod.test_client()
