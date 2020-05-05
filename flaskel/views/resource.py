import flask
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from flaskel import httpcode
from flaskel.ext import builder


class Resource(MethodView):
    @builder.on_accept()
    def get(self, res_id=None, sub_resource=None):
        """

        :param res_id:
        :param sub_resource:
        :return:
        """
        if res_id is None:
            return self.on_collection()

        if sub_resource is None:
            return self.on_get(res_id)

        try:
            _sub_resource = getattr(self, "sub_{}".format(sub_resource))
            return _sub_resource(res_id)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.on_accept()
    def post(self, res_id=None, sub_resource=None):
        """

        :return:
        """
        if res_id is None:
            return self.on_post()
        try:
            _sub_resource_post = getattr(self, "sub_{}_post".format(sub_resource))
            return _sub_resource_post(res_id)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.no_content
    def delete(self, res_id):
        """

        :param res_id:
        :return:
        """
        return self.on_delete(res_id)

    @builder.on_accept()
    def put(self, res_id):
        """

        :param res_id:
        :return:
        """
        return self.on_put(res_id)

    def on_get(self, res_id):
        """

        :param res_id:
        :return:
        """
        self._not_implemented()

    def on_post(self):
        """

        :return:
        """
        self._not_implemented()

    def on_put(self, res_id):
        """

        :param res_id:
        :return:
        """
        self._not_implemented()

    def on_delete(self, res_id):
        """

        :param res_id:
        :return:
        """
        self._not_implemented()

    def on_collection(self):
        """

        :return:
        """
        self._not_implemented()

    def _not_implemented(self):
        """

        """
        raise NotImplemented

    @classmethod
    def register(cls, app, name, url, pk_type='int', **kwargs):
        """

        :param app: Flask or Blueprint instance
        :param name:
        :param url:
        :param pk_type: type of res_id
        """
        view_func = cls.as_view(name, **kwargs)

        url = url.rstrip('/')
        if not url.startswith('/'):
            url = '/{}'.format(url)

        app.add_url_rule(url, view_func=view_func, methods=['GET', 'POST'])

        app.add_url_rule(
            '{url}/<{type}:res_id>'.format(url=url, type=pk_type),
            view_func=view_func,
            methods=['GET', 'PUT', 'DELETE']
        )

        app.add_url_rule(
            '{url}/<{type}:res_id>/<sub_resource>'.format(url=url, type=pk_type),
            view_func=view_func,
            methods=['GET', 'POST']
        )


class SQLAResource(Resource):
    def __init__(self, db, model):
        """

        :param db:
        :param model:
        """
        self._db = db
        self._model = model

    def on_get(self, res_id):
        """

        :param res_id:
        """
        res = self.query.get_or_404(res_id)
        return res.to_dict()

    def on_collection(self, **kwargs):
        """

        :return:
        """
        res_list = []
        for r in self._model.query.filters(**kwargs).all():
            res_list.append(r.to_dict(restricted=True))
        return res_list

    def on_post(self, payload=None):
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

    def on_delete(self, res_id):
        """

        :param res_id:
        """
        res = self._model.query.get_or_404(res_id)
        res.delete()
        self._db.session.commit()

    def on_put(self, res_id, payload=None):
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
