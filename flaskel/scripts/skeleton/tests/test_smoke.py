from flaskel.tester.mixins import Asserter
# noinspection PyUnresolvedReferences
from . import testapp


def test_app_runs(testapp):
    res = testapp.get('/')
    Asserter.assert_status_code(res)
