import typing as t

import flask
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from flaskel.flaskel import cap, httpcode
from flaskel.utils import PayloadValidator, webargs
from .base import Resource


class CatalogResource(Resource):
    methods_collection = ["GET"]
    methods_resource = ["GET"]
    methods_subresource = ["GET"]

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
        if params is None:
            params = webargs.paginate()

        model = model or self._model
        max_size = cap.config.MAX_PAGE_SIZE
        page = params.get("page")
        size = params.get("page_size")
        size = max(size, max_size or 0) if size else max_size
        order_by = getattr(model, "order_by", None)

        return self.response_paginated(
            model.get_list(
                to_dict=False,
                order_by=order_by,
                page=page,
                page_size=size,
                max_per_page=max_size,
                params=params,
                **kwargs,
            ),
            restricted=not params.get("related", False),
        )

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
    validator = PayloadValidator
    methods_collection = ["GET", "POST"]
    methods_subresource = ["GET", "POST"]
    methods_resource = ["GET", "PUT", "DELETE"]

    def __init__(self, session, model):
        """

        :param session: sqlalchemy session instance
        :param model: sqlalchemy model
        """
        super().__init__(model)
        self._session = session

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

    def _create(self, res):
        try:
            self._session.add(res)
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            flask.abort(httpcode.CONFLICT)
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self._session.rollback()
            flask.abort(httpcode.INTERNAL_SERVER_ERROR)

    def on_post(self, *_, **__):
        """

        :return:
        """
        payload = self.validate(self.post_schema)
        res = self.create_resource(payload)
        self._create(res)
        return res.to_dict(), httpcode.CREATED

    def on_delete(self, res_id, *_, **__):
        """

        :param res_id: resource identifier (primary key value)
        """
        res = self._model.query.get_or_404(res_id)

        try:
            self._session.delete(res)
            self._session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self._session.rollback()
            flask.abort(httpcode.INTERNAL_SERVER_ERROR)

    def _update(self, res):
        try:
            self._session.merge(res)
            self._session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self._session.rollback()
            flask.abort(httpcode.INTERNAL_SERVER_ERROR)

    def on_put(self, res_id, *_, **__):
        """

        :param res_id: resource identifier (primary key value)
        :return:
        """
        payload = self.validate(self.put_schema or self.post_schema)
        res = self._model.query.get_or_404(res_id)
        res = self.update_resource(res, payload)
        self._update(res)
        return res.to_dict()
