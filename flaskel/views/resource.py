import flask
from sqlalchemy.exc import IntegrityError

from flaskel import cap, httpcode
from flaskel.utils import webargs
from .base import Resource


class CatalogResource(Resource):
    methods_collection = ['GET', 'HEAD']
    methods_resource = ['GET', 'HEAD']
    methods_subresource = ['GET', 'HEAD']

    def __init__(self, model):
        self._model = model

    def on_get(self, res_id, *args, **kwargs):
        return self._model.get_one(id=res_id)

    def on_collection(self, params=None, model=None, *args, **kwargs):
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
    """TODO Not tested yet"""
    methods_collection = ['POST', 'GET', 'HEAD']
    methods_subresource = ['POST', 'GET', 'HEAD']
    methods_resource = ['GET', 'HEAD', 'PUT', 'DELETE']

    def __init__(self, db, model):
        """

        :param db:
        :param model:
        """
        super().__init__(model)
        self._db = db

    def on_post(self, payload=None, *args, **kwargs):
        """

        :param payload:
        :return:
        """
        res = self._model(**(payload or {}))
        try:
            self._db.session.add()
            self._db.session.commit()
        except IntegrityError:
            self._db.session.rollback()
            flask.abort(httpcode.CONFLICT)
        finally:
            self._db.session.close()

        return res.to_dict(), httpcode.CREATED

    def on_delete(self, res_id, *args, **kwargs):
        """

        :param res_id:
        """
        res = self._model.query.get_or_404(res_id)
        res.delete()
        self._db.session.commit()

    def on_put(self, res_id, payload=None, *args, **kwargs):
        """

        :param res_id:
        :param payload:
        :return:
        """
        res = self._model.query.get_or_404(res_id)
        res.update(**(payload or {}))
        self._db.session.add(res)
        self._db.session.commit()
        return res.to_dict()
