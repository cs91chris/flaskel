from vbcore.date_helper import DateHelper
from vbcore.tester.mixins import Asserter

from flaskel.ext.default import date_helper


def test_init_app(flaskel_app):
    date_helper.init_app(flaskel_app)
    Asserter.assert_equals(flaskel_app.extensions["date_helper"], date_helper)
    Asserter.assert_equals(date_helper.iso_format, DateHelper.DATE_ISO_FORMAT)
