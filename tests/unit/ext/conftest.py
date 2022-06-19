from unittest.mock import MagicMock

import pytest
from pymongo import DESCENDING

from flaskel.ext.mongo import BaseRepo


class MongoRepo(BaseRepo):
    mock_conn = MagicMock()
    collection_key = "test_collection_key"
    sort_by = [("test_key", DESCENDING)]
    projection_detail = ["test_key"]

    @classmethod
    def connection(cls, collection=None):
        return cls.mock_conn


@pytest.fixture
def mongo_repo():
    MongoRepo.mock_conn = MagicMock()
    return MongoRepo
