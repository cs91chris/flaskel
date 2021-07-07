from flaskel.tester.mixins import Asserter
# noinspection PyUnresolvedReferences
from . import auth_token, h, test_client


def test_app_runs(test_client):
    res = test_client.get('/')
    Asserter.assert_status_code(res, h.httpcode.NOT_FOUND)
