from vbcore.http import httpcode

from flaskel.tester.helpers import get_api_tester


def test_api_runs(testapp):
    client = testapp().test_client()
    get_api_tester(client, url="/", subdomain="api", status=httpcode.NOT_FOUND)


def test_web_runs(testapp):
    client = testapp().test_client()
    get_api_tester(client, url="/", status=httpcode.NOT_FOUND)


def test_spa_runs(testapp):
    client = testapp().test_client()
    get_api_tester(client, url="/webapp", status=httpcode.NOT_FOUND)
