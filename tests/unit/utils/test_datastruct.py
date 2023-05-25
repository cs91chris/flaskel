import pytest
from vbcore.tester.asserter import Asserter

from flaskel.utils.datastruct import Pagination


@pytest.mark.parametrize(
    "pagination, expected",
    [
        (Pagination(max_page_size=10), 10),
        (Pagination(page_size=10), 10),
        (Pagination(page_size=10, max_page_size=20), 10),
        (Pagination(page_size=20, max_page_size=10), 10),
        (Pagination(page_size=0, max_page_size=10), 10),
    ],
)
def test_pagination_per_page(pagination, expected):
    Asserter.assert_equals(pagination.per_page(), expected)


@pytest.mark.parametrize(
    "pagination, total, expected",
    [
        (Pagination(max_page_size=10), 100, 10),
        (Pagination(page_size=10), 100, 10),
        (Pagination(page_size=9), 102, 12),
        (Pagination(page_size=10, max_page_size=20), 100, 10),
        (Pagination(page_size=20, max_page_size=10), 100, 10),
        (Pagination(page_size=0, max_page_size=10), 100, 10),
    ],
)
def test_pagination_pages(pagination, total, expected):
    Asserter.assert_equals(pagination.pages(total), expected)


@pytest.mark.parametrize(
    "pagination, total, expected",
    [
        (Pagination(page_size=10), 100, True),
        (Pagination(page_size=100), 100, False),
        (Pagination(page=1, page_size=10), 100, True),
        (Pagination(page=10, page_size=10), 100, False),
    ],
)
def test_pagination_is_paginated(pagination, total, expected):
    Asserter.assert_equals(pagination.is_paginated(total), expected)


@pytest.mark.parametrize(
    "pagination, expected",
    [
        (Pagination(), 0),
        (Pagination(page=1, page_size=10), 0),
        (Pagination(page=3, page_size=100), 200),
        (Pagination(page=100, page_size=100), 9900),
    ],
)
def test_pagination_offset(pagination, expected):
    Asserter.assert_equals(pagination.offset(), expected)
