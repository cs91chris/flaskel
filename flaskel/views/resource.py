import typing as t

import flask
from sqlalchemy.exc import SQLAlchemyError

from flaskel import cap, httpcode, ExtProxy, HttpMethod
from flaskel.ext.default import builder
from flaskel.ext.sqlalchemy import SQLASupport
from flaskel.ext.sqlalchemy.exceptions import DBError
from flaskel.utils import PayloadValidator, webargs
from .base import Resource


class CatalogResource(Resource):
    pagination_enabled: bool = True

    methods_collection = [
        HttpMethod.GET,
    ]
    methods_resource = [
        HttpMethod.GET,
    ]
    methods_subresource = [
        HttpMethod.GET,
    ]

    def __init__(self, model):
        """

        :param model: SqlAlchemy model class
        """
        self._model = model

    def on_get(self, res_id, *_, model=None, **kwargs):
        """
        Get resource info

        :param res_id: resource identifier (primary key value)
        :param model: alternative SqlAlchemy model class
        :param kwargs: extra query filters
        :return:
        """
        model = model or self._model
        return model.get_one(id=res_id, **kwargs)

    def on_collection(self, *_, params=None, model=None, **kwargs):
        """
        Resource collection paginated and sorted

        :param params: parameters (usually from query string)
        :param model: alternative SqlAlchemy model class
        :param kwargs: extra query filters
        :return:
        """
        page = size = None
        model = model or self._model
        max_size = cap.config.MAX_PAGE_SIZE
        order_by = getattr(model, "order_by", None)

        if params is None:
            params = webargs.paginate()

        if self.pagination_enabled is True:
            page = params.get("page")
            size = params.get("page_size")
            size = max(size, max_size or 0) if size else max_size

        response = model.get_list(
            to_dict=not self.pagination_enabled,
            order_by=order_by,
            page=page,
            page_size=size,
            max_per_page=max_size,
            params=params,
            **kwargs,
        )

        if self.pagination_enabled is True:
            return self.response_paginated(
                response,
                restricted=not params.get("related", False),
            )
        return response

    def response_paginated(self, res, **kwargs):
        """
        Prepare the paginated response for resource collection

        :param res: list of sqlalchemy models
        :return:
        """
        if isinstance(res, list):
            return [r.to_dict(**kwargs) for r in res]

        return (
            [r.to_dict(**kwargs) for r in res.items],
            httpcode.PARTIAL_CONTENT if res.has_next else httpcode.SUCCESS,
            self.pagination_headers(res),
        )

    @staticmethod
    def pagination_headers(data):
        return {
            "X-Pagination-Count": data.total,
            "X-Pagination-Page": data.page,
            "X-Pagination-Num-Pages": data.pages,
            "X-Pagination-Page-Size": data.per_page,
        }


class Restful(CatalogResource):
    post_schema: t.Any = None
    put_schema: t.Any = None
    validator: t.Type[PayloadValidator] = PayloadValidator
    support_class: t.Type[SQLASupport] = SQLASupport

    methods_subresource = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]
    methods_collection = [
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
    ]
    methods_resource = [
        HttpMethod.GET,
        HttpMethod.PUT,
        HttpMethod.DELETE,
    ]

    def __init__(self, model, session=None):
        """

        :param session: sqlalchemy session instance
        :param model: sqlalchemy model
        """
        super().__init__(model)
        self._session = session or ExtProxy("sqlalchemy.db.session")
        self.support = self.support_class(self._model, self._session)

    def validate(self, schema):
        """

        :param schema: schema compatible with self validator
        :return:
        """
        schema = schema() if callable(schema) else schema
        return self.validator.validate(schema)

    def create_resource(self, data):
        """

        :param data: dictionary data that represents the resource
        :return: sqlalchemy model instance
        """
        return self._model(**data)

    # noinspection PyMethodMayBeStatic
    def update_resource(self, resource, data):  # pylint: disable=no-self-use
        """

        :param resource: sqlalchemy model instance
        :param data: dictionary data that represents the resource
        :return:
        """
        resource.update(data)
        return resource

    def _session_exception_handler(self, exception: SQLAlchemyError):
        """

        :param exception:
        """
        cap.logger.exception(exception)
        self._session.rollback()

        if isinstance(exception, DBError):
            flask.abort(httpcode.CONFLICT, response={"cause": exception.as_dict()})
        flask.abort(httpcode.INTERNAL_SERVER_ERROR)

    def _create(self, res):
        try:
            self._session.add(res)
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session_exception_handler(exc)

    def _update(self, res):
        try:
            self._session.merge(res)
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session_exception_handler(exc)

    @classmethod
    def _prepare_upsert_filters(cls, *_, **__):
        return {}

    def _upsert(self, data):
        try:
            res, created = self.support.update_or_create(
                data, **self._prepare_upsert_filters(data)
            )
            self._session.commit()
        except SQLAlchemyError as exc:
            return self._session_exception_handler(exc)

        return res, httpcode.CREATED if created else httpcode.SUCCESS

    def on_post(self, *_, **__):
        """

        :return:
        """
        payload = self.validate(self.post_schema)
        res = self.create_resource(payload)
        self._create(res)
        return res.to_dict(), httpcode.CREATED

    def _delete(self, res_id, *_, **__):
        """

        :param res_id: resource identifier (primary key value)
        """
        res = self._model.query.get_or_404(res_id)
        data = res.to_dict()

        try:
            self._session.delete(res)
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session_exception_handler(exc)

        return data

    def on_delete(self, res_id, *args, **kwargs):
        self._delete(res_id, *args, **kwargs)

    def on_put(self, *_, res_id=None, **__):
        """

        :param res_id: resource identifier (primary key value)
            it is optional in order to implement upsert
        :return:
        """
        payload = self.validate(self.put_schema or self.post_schema)

        if res_id is not None:
            res = self._model.query.get_or_404(res_id)
            res = self.update_resource(res, payload)
            self._update(res)
            return res.to_dict()

        res, status = self._upsert(payload)
        return res.to_dict(), status


class PatchApiView(Restful):
    methods_subresource = None
    methods_collection = None
    methods_resource = None
    methods = [
        HttpMethod.PATCH,
    ]

    @classmethod
    def register(cls, app, name=None, urls=(), **kwargs):
        view_func = cls.as_view(name, **kwargs)
        for url in urls:
            cls.normalize_url(url)
            app.add_url_rule(url, view_func=view_func, methods=cls.methods)
        return view_func

    @builder.no_content
    def patch(self, *args, **kwargs):
        return self.on_patch(*args, **kwargs)

    def on_patch(self, *_, **__):
        return self.not_implemented()
