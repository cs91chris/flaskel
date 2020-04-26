import os

import pytest
from flask.testing import FlaskClient

from .blueprints import BLUEPRINTS
from flaskel.ext import EXTENSIONS
from flaskel.patch import ForceHttps
from flaskel import default_app_factory

SKEL_DIR = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'skeleton')


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
    os.environ['APP_CONFIG_FILE'] = os.path.join(os.path.join(SKEL_DIR, 'config'), 'production.py')

    _app = default_app_factory(
        conf_map=dict(TESTING=True),
        blueprints=BLUEPRINTS + (None,) + ((None,),),  # NB: needed to complete coverage
        extensions=EXTENSIONS + (None,) + ((None,),),  # NB: needed to complete coverage
        jinja_fs_loader=["skeleton/templates"],
        static_folder="skeleton/static"
    )

    _app.wsgi_app = ForceHttps(_app.wsgi_app)
    _app.test_client_class = TestClient
    return _app


@pytest.fixture
def app_dev():
    """

    """
    os.environ['APP_CONFIG_FILE'] = os.path.join(os.path.join(SKEL_DIR, 'config'), 'development.py')

    _app = default_app_factory(
        blueprints=BLUEPRINTS,
        extensions=EXTENSIONS,
        template_folder="skeleton/templates",
        static_folder="skeleton/static"
    )

    _app.test_client_class = TestClient
    return _app


@pytest.fixture
def testapp(app_prod):
    """

    :param app_prod:
    :return:
    """
    return app_prod.test_client()
