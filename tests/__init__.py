import os

import pytest
from flask.testing import FlaskClient

from flaskel import default_app_factory
from flaskel.ext import BASE_EXTENSIONS
from flaskel.ext.crypto import Argon2
from flaskel.ext.healthcheck import health_checks, health_mongo, health_redis, health_sqlalchemy
from flaskel.ext.sqlalchemy import db as dbsqla
from flaskel.ext.useragent import UserAgent
from flaskel.patch import ForceHttps
from tests.blueprints import BLUEPRINTS

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
SKEL_DIR = os.path.join(BASE_DIR, 'skeleton')
CONF_DIR = os.path.join(SKEL_DIR, 'config')


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
    os.environ['APP_CONFIG_FILE'] = os.path.join(CONF_DIR, 'production.py')

    def test_health_true(**kwargs):
        return True, None

    def test_health_false(**kwargs):
        return False, "error"

    extra_ext = {
        "empty": (None, (None,)),  # NB: needed to complete coverage
        "useragent": (UserAgent(),),
        "argon2": (Argon2(),),
        "health_checks": (health_checks, {'extensions': (
            {
                'name': 'health_true',
                'func': test_health_true,
            },
            {
                'func': test_health_false,
            },
        )},),
    }

    health_checks.register('mongo', db=dbsqla)(health_mongo)
    health_checks.register('redis', db=dbsqla)(health_redis)
    health_checks.register('sqlalchemy', db=dbsqla)(health_sqlalchemy)

    _app = default_app_factory(
        conf_map=dict(TESTING=True),
        blueprints=(*BLUEPRINTS, *(None,), *((None,),)),  # NB: needed to complete coverage
        extensions={**BASE_EXTENSIONS, **extra_ext},
        jinja_fs_loader=["skeleton/templates"],
        static_folder="skeleton/static"
    )

    _app.wsgi_app = ForceHttps(_app.wsgi_app)
    _app.test_client_class = TestClient
    _app.config['USER_AGENT_AUTO_PARSE'] = True
    return _app


@pytest.fixture
def app_dev():
    """

    """
    os.environ['APP_CONFIG_FILE'] = os.path.join(CONF_DIR, 'development.py')

    _app = default_app_factory(
        blueprints=BLUEPRINTS,
        extensions=BASE_EXTENSIONS,
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
