# noinspection PyUnresolvedReferences
from . import auth_token, h, test_client


def test_app_runs(test_client):
    h.api_tester(test_client, '/', status=h.httpcode.NOT_FOUND)
