from unittest.mock import MagicMock

from bson import ObjectId
from pymongo import DESCENDING
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum
from vbcore.tester.mixins import Asserter

from flaskel.ext.mongo import BaseRepo, FlaskMongoDB, Pagination, PaginationData


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


class MongoRepo(BaseRepo):
    mock_conn = MagicMock()
    collection_key = "test_collection_key"
    sort_by = [("test_key", DESCENDING)]
    projection_detail = ["test_key"]

    @classmethod
    def connection(cls, collection=None):
        return cls.mock_conn


def test_repo_count():
    MongoRepo.count(filters={"key": "value"})
    MongoRepo.mock_conn.count_documents.assert_called_once_with({"key": "value"})


def test_repo_aggregate():
    stages = [{"stage": "a"}, {"stage": "b"}]
    MongoRepo.aggregate(stages=stages)
    MongoRepo.mock_conn.aggregate.assert_called_once_with(stages)


def test_repo_delete():
    res_id = "62acdef1efe39de177afaf24"
    MongoRepo.delete(res_id, filter_key="filter_value")
    MongoRepo.mock_conn.delete_one.assert_called_once_with(
        {"_id": ObjectId(res_id), "filter_key": "filter_value"},
    )


def test_repo_get_detail():
    res_id = "62acdef1efe39de177afaf24"
    MongoRepo.get_detail(res_id, filters={"filter_key": "filter_value"})
    MongoRepo.mock_conn.find_one_or_404.assert_called_once_with(
        {"_id": ObjectId(res_id), "filter_key": "filter_value"},
        MongoRepo.projection_detail,
        sort=MongoRepo.sort_by,
    )


def test_repo_get_list():
    MongoRepo.get_list(filters={"key": "value"})
    MongoRepo.mock_conn.find.assert_called_once_with(
        {"key": "value"}, None, sort=MongoRepo.sort_by
    )


def test_repo_compute_pagination():
    pagination = MongoRepo.compute_pagination(100, Pagination(page_size=10, page=2))
    Asserter.assert_equals(
        pagination,
        PaginationData(
            limit=10,
            skip=10,
            status=httpcode.PARTIAL_CONTENT,
            headers={
                HeaderEnum.X_PAGINATION_PAGE: 2,
                HeaderEnum.X_PAGINATION_NUM_PAGES: 10,
                HeaderEnum.X_PAGINATION_PAGE_SIZE: 10,
                HeaderEnum.X_PAGINATION_COUNT: 100,
            },
        ),
    )


def test_repo_response_paginated():
    query = MagicMock()
    query.skip.return_value = query

    _, status, headers = MongoRepo.response_paginated(
        query, 100, Pagination(page_size=10, page=3)
    )
    query.skip.assert_called_once_with(20)
    query.limit.assert_called_once_with(10)

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
