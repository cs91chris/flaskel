from .helpers import h


def test_app_runs(test_client):
    h.api_tester(test_client, "/", status=h.httpcode.NOT_FOUND)
