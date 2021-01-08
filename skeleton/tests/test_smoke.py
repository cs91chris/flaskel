# noinspection PyUnresolvedReferences
from flaskel.tester import Asserter, HttpAsserter
# noinspection PyUnresolvedReferences
from . import testapp


def test_app_runs(testapp):
    res = testapp.get('/')
    HttpAsserter.assert_status_code(res)
