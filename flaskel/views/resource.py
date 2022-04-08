import typing as t

from sqlalchemy.exc import SQLAlchemyError
from vbcore.db.exceptions import DBError
from vbcore.db.support import SQLASupport
from vbcore.http import httpcode, HttpMethod
from vbcore.http.headers import HeaderEnum

from flaskel import abort, cap, db_session, PayloadValidator, webargs
from flaskel.ext.default import builder

from .base import BaseView, Resource, UrlsType


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
        self._model = model

    def on_get(self, res_id, *_, model=None, **kwargs):
        """
        Get resource info

        :param res_id: resource identifier (primary key value)
        :param model: alternative SQLAlchemy model class
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
        max_size = cap.config.PAGINATION_MAX_PAGE_SIZE
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
            (httpcode.PARTIAL_CONTENT if res.has_next else httpcode.SUCCESS),
            self.pagination_headers(res),
        )

    @staticmethod
    def pagination_headers(data) -> t.Dict[str, int]:
        return {
            HeaderEnum.X_PAGINATION_COUNT: data.total,
            HeaderEnum.X_PAGINATION_PAGE: data.page,
            HeaderEnum.X_PAGINATION_NUM_PAGES: data.pages,
            HeaderEnum.X_PAGINATION_PAGE_SIZE: data.per_page,
        }


class Restful(CatalogResource):
    post_schema: t.Any = None
    put_schema: t.Any = None
    support_class: t.Type[SQLASupport] = SQLASupport
    validator: t.Type[PayloadValidator] = PayloadValidator

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

    def __init__(self, model, session=db_session):
        """

        :param session: sqlalchemy session instance
        :param model: sqlalchemy model
        """
        super().__init__(model)
        self._session = session
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

    def _session_exception_handler(self, exception: SQLAlchemyError) -> t.NoReturn:
        cap.logger.exception(exception)
        self._session.rollback()

        if isinstance(exception, DBError):
            abort(httpcode.CONFLICT, response={"cause": exception.as_dict()})
        abort(httpcode.INTERNAL_SERVER_ERROR)

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
    def _prepare_upsert_filters(cls, *_, **__) -> t.Dict[str, t.Any]:
        return {}

    def _upsert(self, data) -> t.Tuple[t.Any, int]:
        try:
            res, created = self.support.update_or_create(
                data, **self._prepare_upsert_filters(data)
            )
            self._session.commit()
            return res, httpcode.CREATED if created else httpcode.SUCCESS
        except SQLAlchemyError as exc:
            return t.cast(t.Tuple[t.Any, int], self._session_exception_handler(exc))

    def on_post(self, *_, **__) -> t.Tuple[t.Dict[str, t.Any], int]:
        payload = self.validate(self.post_schema)
        res = self.create_resource(payload)
        self._create(res)
        return res.to_dict(), httpcode.CREATED

    def _delete(self, res_id, *_, **__) -> t.Dict[str, t.Any]:
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

    def on_put(self, *_, res_id=None, **__) -> t.Tuple[t.Dict[str, t.Any], int]:
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
            return res.to_dict(), httpcode.SUCCESS

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
    def register(
        cls,
        app,
        name: t.Optional[str] = None,
        urls: UrlsType = (),
        view: t.Optional[t.Type[BaseView]] = None,
        **kwargs,
    ) -> t.Callable:
        return BaseView.register(app, name, urls, view)

    @builder.no_content
    def patch(self, *args, **kwargs):
        return self.on_patch(*args, **kwargs)

    def on_patch(self, *_, **__):
        return self.not_implemented()
