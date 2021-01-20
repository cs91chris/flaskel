import flask
from flask.views import MethodView, View

from flaskel import httpcode
from flaskel.ext import builder


class BaseView(View):
    methods = ['GET']

    def dispatch_request(self):
        """
        Must be implemented in every subclass
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def register(cls, app, name, *urls, **kwargs):
        """

        :param app: Flask app or blueprint
        :param name: optional view name
        :param urls: optional urls or view name
        :param kwargs: argument passed to cls constructor
        """
        name = name or cls.__name__
        view_func = cls.as_view(name, **kwargs)
        for u in urls or (f"/{name}",):
            app.add_url_rule(u, view_func=view_func, methods=cls.methods)


class Resource(MethodView):
    @builder.on_accept()
    def get(self, *args, res_id=None, sub_resource=None, **kwargs):
        """

        :param res_id:
        :param sub_resource:
        :return:
        """
        if res_id is None:
            return self.on_collection(*args, **kwargs)

        if sub_resource is None:
            return self.on_get(res_id, *args, **kwargs)

        try:
            _sub_resource = getattr(self, "sub_{}".format(sub_resource))
            return _sub_resource(res_id, *args, **kwargs)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.on_accept()
    def post(self, *args, res_id=None, sub_resource=None, **kwargs):
        """

        :param res_id:
        :param sub_resource
        :return:
        """
        if res_id is None:
            return self.on_post(*args, **kwargs)
        try:
            _sub_resource_post = getattr(self, "sub_{}_post".format(sub_resource))
            return _sub_resource_post(res_id, *args, **kwargs)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.no_content
    def delete(self, res_id, *args, **kwargs):
        """

        :param res_id:
        :return:
        """
        return self.on_delete(res_id, *args, **kwargs)

    @builder.on_accept()
    def put(self, res_id, *args, **kwargs):
        """

        :param res_id:
        :return:
        """
        return self.on_put(res_id, *args, **kwargs)

    def on_get(self, res_id, *args, **kwargs):
        self._not_implemented()  # pragma: no cover

    def on_post(self, *args, **kwargs):
        self._not_implemented()  # pragma: no cover

    def on_put(self, res_id, *args, **kwargs):
        self._not_implemented()  # pragma: no cover

    def on_delete(self, res_id, *args, **kwargs):
        self._not_implemented()  # pragma: no cover

    def on_collection(self, *args, **kwargs):
        self._not_implemented()  # pragma: no cover

    # noinspection PyMethodMayBeStatic
    def _not_implemented(self):  # pragma: no cover
        flask.abort(httpcode.NOT_IMPLEMENTED)

    @classmethod
    def register(cls, app, name=None, url=None, pk_type='int', **kwargs):
        """

        :param app: Flask or Blueprint instance
        :param name: view name
        :param url: url to bind
        :param pk_type: type of res_id
        """
        name = name or cls.__name__
        url = url or f"/{name}"
        view_func = cls.as_view(name, **kwargs)
        url = f"/{url.rstrip('/')}"

        app.add_url_rule(
            url,
            view_func=view_func,
            methods=['GET', 'POST']
        )
        app.add_url_rule(
            f"{url}/<{pk_type}:res_id>",
            view_func=view_func,
            methods=['GET', 'PUT', 'DELETE']
        )
        app.add_url_rule(
            f"{url}/<{pk_type}:res_id>/<sub_resource>",
            view_func=view_func,
            methods=['GET', 'POST']
        )
