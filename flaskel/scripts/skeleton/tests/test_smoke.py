# flake8: noqa F405
# pylint: disable=redefined-outer-name

from . import helpers as h


def test_app_runs(test_client):
    h.api_tester(test_client, "/", status=h.httpcode.NOT_FOUND)
