from decimal import Decimal

import pytest
from vbcore.tester.mixins import Asserter
from werkzeug.routing import Map, ValidationError

from flaskel.converters import ListConverter, DecimalConverter


def test_list_converter():
    converter = ListConverter(Map())
    Asserter.assert_equals(converter.to_python("a+b+c"), ["a", "b", "c"])
    Asserter.assert_equals(converter.to_url(["a", "b", "c"]), "a%2Bb%2Bc")


def test_decimal_converter():
    converter = DecimalConverter(Map())
    Asserter.assert_equals(converter.to_python("-123.456"), Decimal("-123.456"))
    Asserter.assert_equals(converter.to_url(Decimal("-123.456")), "-123.456")


def test_decimal_converter_unsigned():
    converter = DecimalConverter(Map(), signed=False)
    Asserter.assert_equals(converter.to_python("-123.456"), Decimal("-123.456"))
    Asserter.assert_equals(converter.to_url(Decimal("-123.456")), "-123.456")


def test_decimal_converter_range():
    converter = DecimalConverter(Map(), min=0, max=1.0)
    Asserter.assert_equals(converter.to_python("0.1"), Decimal("0.1"))
    Asserter.assert_equals(converter.to_url(Decimal("0.1")), "0.1")

    with pytest.raises(ValidationError):
        converter.to_python("1.1")