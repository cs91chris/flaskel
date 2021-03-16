import os

import pytest

from flaskel import TestClient
from flaskel.utils import yaml
from scripts.cli import APP_CONFIG

yaml.setup_yaml_parser()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONF_FILE = os.path.join(BASE_DIR, '..', 'config', 'conf.yaml')
CONFIG = yaml.load_yaml_file(CONF_FILE)

EXTRAS = dict(
    conf=CONFIG.app,
    template_folder="blueprints/web/templates",
    static_folder="blueprints/web/static"
)


@pytest.fixture(scope='session')
def testapp():
    return TestClient.get_app(**{**APP_CONFIG, **EXTRAS}).test_client()
