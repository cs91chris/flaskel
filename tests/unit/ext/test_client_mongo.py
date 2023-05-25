from unittest.mock import MagicMock

from bson import ObjectId
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum
from vbcore.tester.asserter import Asserter

from flaskel.ext.mongo import FlaskMongoDB, Pagination


def test_init_app(flaskel_app):
    timeout = 1
    app = flaskel_app
    app.config.APP_NAME = "TEST_APP"
    app.config.MONGO_OPTS = ObjectDict(timeout=timeout)

    client_mongo = FlaskMongoDB()
    client_mongo.init_app(app)

    Asserter.assert_equals(app.extensions["mongo"]["default"], client_mongo)
    Asserter.assert_equals(app.config.MONGO_URI, "mongodb://localhost")
    Asserter.assert_equals(
        app.config.MONGO_OPTS,
        {
            "appname": app.config.APP_NAME,
            "directConnection": False,
            "minPoolSize": 0,
            "maxPoolSize": 100,
            "maxConnecting": 2,
            "retryWrites": True,
            "retryReads": True,
            "maxIdleTimeMS": None,
            "waitQueueTimeoutMS": None,
            "document_class": ObjectDict,
            "socketTimeoutMS": timeout,
            "connectTimeoutMS": timeout,
            "serverSelectionTimeoutMS": timeout,
            "heartbeatFrequencyMS": 10000,
        },
    )


def test_repo_count(mongo_repo):
    mongo_repo.count(filters={"key": "value"})
    mongo_repo.mock_conn.count_documents.assert_called_once_with({"key": "value"})


def test_repo_aggregate(mongo_repo):
    stages = [{"stage": "a"}, {"stage": "b"}]
    mongo_repo.aggregate(stages=stages)
    mongo_repo.mock_conn.aggregate.assert_called_once_with(stages)


def test_repo_delete(mongo_repo):
    res_id = "62acdef1efe39de177afaf24"
    mongo_repo.delete(res_id, filter_key="filter_value")
    mongo_repo.mock_conn.delete_one.assert_called_once_with(
        {"_id": ObjectId(res_id), "filter_key": "filter_value"},
    )


def test_repo_get_detail(mongo_repo):
    res_id = "62acdef1efe39de177afaf24"
    mongo_repo.get_detail(res_id, filters={"filter_key": "filter_value"})
    mongo_repo.mock_conn.find_one_or_404.assert_called_once_with(
        {"_id": ObjectId(res_id), "filter_key": "filter_value"},
        mongo_repo.projection_detail,
        sort=mongo_repo.sort_by,
    )


def test_repo_get_list(mongo_repo):
    mongo_repo.get_list(filters={"key": "value"})
    mongo_repo.mock_conn.find.assert_called_once_with(
        {"key": "value"}, None, sort=mongo_repo.sort_by
    )


def test_repo_get_list_paginated(mongo_repo):
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    mongo_repo.mock_conn.find.return_value = cursor
    mongo_repo.mock_conn.count_documents.return_value = 100

    filters = {"key": "value"}

    _, status, headers = mongo_repo.get_list(
        filters=filters, pagination=Pagination(page_size=10, page=3)
    )

    mongo_repo.mock_conn.count_documents.assert_called_once_with(filters)
    mongo_repo.mock_conn.find.assert_called_once_with(
        filters, None, sort=mongo_repo.sort_by
    )
    cursor.skip.assert_called_once_with(20)
    cursor.limit.assert_called_once_with(10)

    Asserter.assert_equals(status, httpcode.PARTIAL_CONTENT)
    Asserter.assert_equals(
        headers,
        {
            HeaderEnum.X_PAGINATION_PAGE: 3,
            HeaderEnum.X_PAGINATION_NUM_PAGES: 10,
            HeaderEnum.X_PAGINATION_PAGE_SIZE: 10,
            HeaderEnum.X_PAGINATION_COUNT: 100,
        },
    )
