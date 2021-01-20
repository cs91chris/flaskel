import flask
from sqlalchemy.exc import IntegrityError

from flaskel import httpcode
from .base import Resource


class CatalogResource(Resource):
    def __init__(self, model):
        self._model = model

    def on_get(self, res_id, *args, **kwargs):
        return self._model.get_one(id=res_id)

    def on_collection(self, *args, **kwargs):
        res = self._model.get_list(to_dict=False)
        restricted = False if flask.request.args.get('_related') else True
        return [r.to_dict(restricted=restricted) for r in res]


class Restful(CatalogResource):
    """TODO Not tested yet"""

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
