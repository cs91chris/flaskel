import flask
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from flaskel.flaskel import cap, httpcode
from flaskel.utils import PayloadValidator, webargs
from .base import Resource


class CatalogResource(Resource):
    methods_collection = ['GET']
    methods_resource = ['GET']
    methods_subresource = ['GET']

    def __init__(self, model):
        """

        :param model: SqlAlchemy model class
        """
        self._model = model

    def on_get(self, res_id, model=None, *args, **kwargs):
        """
        Get resource info

        :param res_id: resource identifier (primary key value)
        :param model: alternative SqlAlchemy model class
        :param kwargs: extra query filters
        :return:
        """
        model = model or self._model
        return model.get_one(id=res_id, **kwargs)

    def on_collection(self, params=None, model=None, *args, **kwargs):
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
        page = params.get('page')
        size = params.get('page_size') or max_size
        order_by = getattr(model, 'order_by', None)

        return self.response_paginated(
            model.get_list(
                to_dict=False, order_by=order_by, page=page,
                page_size=size, max_per_page=max_size, **kwargs
            ),
            restricted=not params.get('related', False)
        )

    def response_paginated(self, res, **kwargs):
        """
        Prepare the paginated response for resource collection

        :param res: list of sqlalchemy models
        :return:
        """
        if type(res) is list:
            return [r.to_dict(**kwargs) for r in res]

        return (
            [r.to_dict(**kwargs) for r in res.items],
            httpcode.PARTIAL_CONTENT if res.has_next else httpcode.SUCCESS,
            self.pagination_headers(res)
        )

    @staticmethod
    def pagination_headers(data):
        return {
            'X-Pagination-Count':     data.total,
            'X-Pagination-Page':      data.page,
            'X-Pagination-Num-Pages': data.pages,
            'X-Pagination-Page-Size': data.per_page,
        }


class Restful(CatalogResource):
    post_schema = None
    put_schema = None
    validator = PayloadValidator
    methods_collection = ['GET', 'POST']
    methods_subresource = ['GET', 'POST']
    methods_resource = ['GET', 'PUT', 'DELETE']

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
    def update_resource(self, resource, data):
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

        return res.to_dict(), httpcode.CREATED

    def on_post(self, *args, **kwargs):
        """

        :return:
        """
        payload = self.validate(self.post_schema)
        res = self.create_resource(payload)
        return self._create(res)

    def on_delete(self, res_id, *args, **kwargs):
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

        return res.to_dict()

    def on_put(self, res_id, *args, **kwargs):
        """

        :param res_id: resource identifier (primary key value)
        :return:
        """
        payload = self.validate(self.put_schema)
        res = self._model.query.get_or_404(res_id)
        res = self.update_resource(res, payload)
        return self._update(res)
