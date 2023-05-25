from vbcore.date_helper import DateTimeFmt
from vbcore.tester.asserter import Asserter

from flaskel.ext.default import date_helper


def test_init_app(flaskel_app):
    date_helper.init_app(flaskel_app)
    Asserter.assert_equals(flaskel_app.extensions["date_helper"], date_helper)
    Asserter.assert_equals(date_helper.iso_format, DateTimeFmt.ISO)
