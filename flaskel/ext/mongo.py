import typing as t
from dataclasses import dataclass
from functools import partial
from math import ceil

from bson import ObjectId
from flask_pymongo import PyMongo
from flask_pymongo.wrappers import Collection
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult
from vbcore.datastruct import ObjectDict
from vbcore.date_helper import Seconds
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum

from flaskel import client_mongo, ConfigProxy


class FlaskMongoDB(PyMongo):
    def init_app(self, app, *args, ext_name: str = "default", **kwargs):
        self.set_default_config(app, **kwargs)
        super().init_app(app, *args, **app.config.MONGO_OPTS)
        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["mongo"] = ObjectDict()
        app.extensions["mongo"][ext_name] = self

    @classmethod
    def set_default_config(cls, app, **kwargs):
        app.config.setdefault("MONGO_URI", "mongodb://localhost")
        app.config.setdefault("MONGO_OPTS", {})

        timeout = app.config.MONGO_OPTS.pop("timeout", None)
        default_timeout = timeout or Seconds.millis

        app.config.MONGO_OPTS.setdefault("appname", app.config.APP_NAME)
        app.config.MONGO_OPTS.setdefault("directConnection", False)
        app.config.MONGO_OPTS.setdefault("minPoolSize", 0)
        app.config.MONGO_OPTS.setdefault("maxPoolSize", 100)
        app.config.MONGO_OPTS.setdefault("maxConnecting", 2)
        app.config.MONGO_OPTS.setdefault("retryWrites", True)
        app.config.MONGO_OPTS.setdefault("retryReads", True)
        app.config.MONGO_OPTS.setdefault("maxIdleTimeMS", None)
        app.config.MONGO_OPTS.setdefault("waitQueueTimeoutMS", None)
        app.config.MONGO_OPTS.setdefault("document_class", ObjectDict)
        app.config.MONGO_OPTS.setdefault("socketTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("connectTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("serverSelectionTimeoutMS", default_timeout)
        app.config.MONGO_OPTS.setdefault("heartbeatFrequencyMS", Seconds.millis * 10)

        app.config.MONGO_OPTS.update(**kwargs)


@dataclass(frozen=True)
class Pagination:
    page: int = 1
    page_size: int = 50
    max_page_size: t.Optional[int] = None


@dataclass(frozen=True)
class PaginationData:
    skip: int
    limit: int
    status: int
    headers: t.Dict[str, int]


ResIdType = t.Union[ObjectId, str]
SortType = t.List[t.Tuple[str, int]]


class BaseRepo:
    sink = client_mongo
    collection_key: str = ""
    collections = ConfigProxy("COLLECTIONS")

    sort_by: t.Optional[SortType] = None
    projection_list: t.Optional[t.List[str]] = None
    projection_detail: t.Optional[t.List[str]] = None

    @classmethod
    def prepare_record(cls, record: dict):
        return record

    @classmethod
    def prepare_collection(cls, collection: t.Optional[str] = None) -> str:
        return cls.collections.get(collection or cls.collection_key)

    @classmethod
    def connection(cls, collection: t.Optional[str] = None) -> Collection:
        return cls.sink[cls.prepare_collection(collection)]

    @classmethod
    def range_filter(cls, flt_from, flt_to) -> dict:
        return {"$gte": flt_from, "$lte": flt_to}

    @classmethod
    def count(
        cls, collection: t.Optional[str] = None, filters: t.Optional[dict] = None
    ) -> int:
        return cls.connection(collection).count_documents(filters or {})

    @classmethod
    def aggregate(
        cls, stages: t.List[dict], collection: t.Optional[str] = None, **kwargs
    ):
        return cls.connection(collection).aggregate(stages, **kwargs)

    @classmethod
    def find(
        cls,
        collection: t.Optional[str] = None,
        filters: t.Optional[dict] = None,
        projection: t.Optional[t.List[str]] = None,
        sort: t.Optional[SortType] = None,
        raise_404: bool = False,
        **kwargs,
    ) -> Cursor:
        conn = cls.connection(collection)
        find = conn.find_one_or_404 if raise_404 else conn.find
        return find(filters or {}, projection, sort=sort, **kwargs)

    @classmethod
    def delete(
        cls,
        res_id: ResIdType,
        collection: t.Optional[str] = None,
        **kwargs,
    ) -> DeleteResult:
        return cls.connection(collection).delete_one(
            {"_id": ObjectId(res_id) if isinstance(res_id, str) else res_id, **kwargs}
        )

    @classmethod
    def get_list(
        cls,
        filters: t.Optional[dict] = None,
        pagination: t.Optional[Pagination] = None,
        projection: t.Optional[t.List[str]] = None,
        sort: t.Optional[SortType] = None,
        collection: t.Optional[str] = None,
        **kwargs,
    ) -> t.Union[t.Tuple[list, int, dict], t.List[dict]]:
        cursor = partial(
            cls.find,
            collection=collection,
            filters=filters,
            projection=projection or cls.projection_list,
            sort=sort or cls.sort_by,
            **kwargs,
        )

        if pagination:
            total = cls.count(collection=collection, filters=filters)
            return cls.response_paginated(cursor() if total else (), total, pagination)

        return [cls.prepare_record(d) for d in cursor()]

    @classmethod
    def get_detail(
        cls,
        res_id: ResIdType,
        filters: t.Optional[dict] = None,
        projection: t.Optional[t.List[str]] = None,
        sort: t.Optional[SortType] = None,
        **kwargs,
    ):
        return cls.find(
            raise_404=True,
            filters={
                "_id": ObjectId(res_id) if isinstance(res_id, str) else res_id,
                **filters,
            },
            projection=projection or cls.projection_detail,
            sort=sort or cls.sort_by,
            **kwargs,
        )

    @classmethod
    def response_paginated(
        cls, query, total: int, pagination: Pagination
    ) -> t.Tuple[list, int, dict]:
        pagination_info = cls.compute_pagination(total, pagination)
        cursor = (
            query.skip(pagination_info.skip).limit(pagination_info.limit)
            if query
            else tuple()
        )
        return (
            [cls.prepare_record(d) for d in cursor],
            pagination_info.status,
            pagination_info.headers,
        )

    @classmethod
    def compute_pagination(cls, total: int, pagination: Pagination) -> PaginationData:
        page = pagination.page
        if pagination.max_page_size:
            page_size = min(pagination.page_size, pagination.max_page_size)
        else:
            page_size = pagination.page_size

        pages = int(ceil(total / float(page_size))) if page_size != 0 else 0

        return PaginationData(
            limit=page_size,
            skip=(page - 1) * page_size,
            status=httpcode.PARTIAL_CONTENT if page < pages else httpcode.SUCCESS,
            headers={
                HeaderEnum.X_PAGINATION_PAGE: page,
                HeaderEnum.X_PAGINATION_NUM_PAGES: pages,
                HeaderEnum.X_PAGINATION_PAGE_SIZE: page_size,
                HeaderEnum.X_PAGINATION_COUNT: total,
            },
        )
