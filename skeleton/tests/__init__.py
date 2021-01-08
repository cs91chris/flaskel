import os

import pytest

from blueprints import BLUEPRINTS
from ext import EXTENSIONS
from flaskel import TestClient
from flaskel.ext import BASE_EXTENSIONS
from flaskel.utils import yaml

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONF_FILE = os.path.join(BASE_DIR, 'config', 'conf.json')

EXTRAS = dict(
    template_folder="blueprints/web/templates",
    static_folder="blueprints/web/static"
)


@pytest.fixture(scope='session')
def testapp():
    return TestClient.get_app(
        conf=yaml.load_yaml_file(CONF_FILE),
        blueprints=BLUEPRINTS,
        extensions={**BASE_EXTENSIONS, **EXTENSIONS},
        **(EXTRAS or {})
    ).test_client()
