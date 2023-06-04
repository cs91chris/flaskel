from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from vbcore.datastruct import ObjectDict
from vbcore.tester.asserter import Asserter

from flaskel.ext.templating import filters

MockedCurrentApp = MagicMock(
    config=ObjectDict(
        NOT_AVAILABLE_DESC="N/A",
        PRETTY_DATE="%d %B %Y %I:%M %p",
        HUMAN_FILE_SIZE_DIVIDER=1000,
        HUMAN_FILE_SIZE_SCALE=["KB", "MB", "GB"],
    )
)


@patch("flaskel.ext.templating.filters.cap", new=MockedCurrentApp)
@pytest.mark.parametrize(
    "missing",
    [
        (),
        [],
        {},
        "",
        None,
    ],
    ids=[
        "empty-tuple",
        "empty-list",
        "empty-dict",
        "empty-string",
        "null",
    ],
)
def test_or_na(missing):
    expected = MockedCurrentApp.config.NOT_AVAILABLE_DESC
    Asserter.assert_equals(filters.or_na(missing), expected)
    Asserter.assert_equals(filters.or_na("aaa"), "aaa")


@patch("flaskel.ext.templating.filters.cap", new=MockedCurrentApp)
@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "no"),
        (False, "no"),
        (True, "yes"),
    ],
)
def test_yes_or_no(value, expected):
    Asserter.assert_equals(filters.yes_or_no(value), expected)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("abcdef", "fedcba"),
        (["a", "b", "c"], ["c", "b", "a"]),
        (("a", "b", "c"), ("c", "b", "a")),
    ],
    ids=[
        "string",
        "list",
        "tuple",
    ],
)
def test_reverse(value, expected):
    Asserter.assert_equals(filters.reverse(value), expected)


@patch("flaskel.ext.templating.filters.cap", new=MockedCurrentApp)
@pytest.mark.parametrize(
    "value",
    [
        datetime(year=2020, month=1, day=1, hour=1),
        "2020-01-01T01:00:00",
        "2020/01/01 01:00:00.00",
    ],
    ids=[
        "datetime",
        "iso-string",
        "custom-string",
    ],
)
def test_pretty_date(value):
    Asserter.assert_equals(filters.pretty_date(value), "01 January 2020 01:00 AM")


def test_order_by_ascending():
    data = [
        {"a": "a-4", "b": 4},
        {"a": "a-2", "b": 2},
        {"a": "a-1", "b": 1},
        {"a": "a-3", "b": 3},
    ]
    expected = [
        {"a": "a-1", "b": 1},
        {"a": "a-2", "b": 2},
        {"a": "a-3", "b": 3},
        {"a": "a-4", "b": 4},
    ]
    Asserter.assert_equals(filters.order_by(data, "b"), expected)


def test_order_by_descending():
    data = [
        {"a": "a-4", "b": 4},
        {"a": "a-2", "b": 2},
        {"a": "a-1", "b": 1},
        {"a": "a-3", "b": 3},
    ]
    expected = [
        {"a": "a-4", "b": 4},
        {"a": "a-3", "b": 3},
        {"a": "a-2", "b": 2},
        {"a": "a-1", "b": 1},
    ]
    Asserter.assert_equals(filters.order_by(data, "b", descending=True), expected)


def test_truncate():
    data = "abcdefgh"
    Asserter.assert_equals(filters.truncate(data, 3), "abc ...")
    Asserter.assert_equals(filters.truncate(data, len(data)), data)


@patch("flaskel.ext.templating.filters.cap", new=MockedCurrentApp)
@pytest.mark.parametrize(
    "value, expected",
    [
        (99, "99 B"),
        (102153021, "102.15 MB"),
        (1021530210000, "1021.53 GB"),
    ],
    ids=[
        "B",
        "MB",
        "GB",
    ],
)
def test_human_byte_size(value, expected):
    Asserter.assert_equals(filters.human_byte_size(value), expected)
