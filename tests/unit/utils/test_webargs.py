from datetime import datetime
from decimal import Decimal

import pytest
from vbcore.datastruct import ObjectDict
from vbcore.tester.asserter import Asserter

from flaskel import webargs
from flaskel.http.exceptions import BadRequest


@pytest.mark.parametrize(
    "field_type, value, expected",
    [
        (webargs.Field.integer, "1", 1),
        (webargs.Field.string, "aaa", "aaa"),
        (webargs.Field.decimal, "1.23", Decimal("1.23")),
        (webargs.Field.boolean, "true", True),
        (webargs.Field.positive, "1", 1),
        (webargs.Field.negative, "-1", -1),
        (webargs.Field.not_positive, "0", 0),
        (webargs.Field.not_negative, "0", 0),
        (
            webargs.Field.isodate,
            "2022-02-15T22:17:09",
            datetime(2022, 2, 15, 22, 17, 9),
        ),
        (webargs.Field.str_list, "a,b,c", ["a", "b", "c"]),
        (webargs.Field.int_list, "1,2,3", [1, 2, 3]),
    ],
    ids=[
        "integer",
        "string",
        "decimal",
        "boolean",
        "positive",
        "negative",
        "not_positive",
        "not_negative",
        "isodate",
        "str_list",
        "int_list",
    ],
)
def test_optional_fields_ok(flaskel_app, field_type, value, expected):
    @webargs.query(ObjectDict(field=field_type()))
    def fake_request(params):
        return params["field"]

    with flaskel_app.test_request_context(path=f"/?field={value}"):
        # pylint: disable=no-value-for-parameter
        Asserter.assert_equals(fake_request(), expected)


@pytest.mark.parametrize(
    "field_type, value, expected",
    [
        (webargs.Field.integer, "a", "Not a valid integer."),
        (webargs.Field.decimal, "aaa", "Not a valid number."),
        (webargs.Field.boolean, "vero", "Not a valid boolean."),
        (webargs.Field.positive, "-1", "Invalid value."),
        (webargs.Field.negative, "1", "Invalid value."),
        (webargs.Field.not_positive, "1", "Invalid value."),
        (webargs.Field.not_negative, "-1", "Invalid value."),
        (
            webargs.Field.isodate,
            "20220215",
            "Not a valid datetime.",
        ),
    ],
    ids=[
        "integer",
        "decimal",
        "boolean",
        "positive",
        "negative",
        "not_positive",
        "not_negative",
        "isodate",
    ],
)
def test_optional_fields_error(flaskel_app, field_type, value, expected):
    @webargs.query(ObjectDict(field=field_type()))
    def fake_request(params):
        return params["field"]

    with pytest.raises(BadRequest) as error:
        with flaskel_app.test_request_context(path=f"/?field={value}"):
            # pylint: disable=no-value-for-parameter
            fake_request()

    response = error.value.response
    Asserter.assert_equals(len(response["query"]["field"]), 1)
    Asserter.assert_equals(response["query"]["field"][0], expected)


def test_paginate_function(flaskel_app):
    with flaskel_app.test_request_context(path="/?page=2&page_size=50"):
        Asserter.assert_equals(
            webargs.paginate(), {"related": False, "page_size": 50, "page": 2}
        )


def test_pagination_decorator(flaskel_app):
    @webargs.paginate
    def pagination(params):
        return params

    with flaskel_app.test_request_context(path="/?page=2&page_size=50"):
        # pylint: disable=no-value-for-parameter
        Asserter.assert_equals(
            pagination(), {"related": False, "page_size": 50, "page": 2}
        )
