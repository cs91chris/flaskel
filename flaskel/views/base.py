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
        view = cls.as_view(name, **kwargs)
        for u in urls or (f"/{name}",):
            app.add_url_rule(u, view_func=view, methods=cls.methods)


class Resource(MethodView):
    methods_collection = ['POST', 'GET']
    methods_resource = ['GET', 'PUT', 'DELETE']
    methods_subresource = ['POST', 'GET']

    @classmethod
    def register(cls, app, name=None, url=None, view=None, pk_type='int', **kwargs):
        """

        :param app: Flask or Blueprint instance
        :param name: view name
        :param url: url to bind
        :param view: view class
        :param pk_type: type of res_id
        """
        _class = view or cls
        name = name or _class.__name__
        view_func = _class.as_view(name, **kwargs)
        url = f"/{(url or name).rstrip('/')}"

        app.add_url_rule(
            url, view_func=view_func,
            methods=cls.methods_collection
        )
        app.add_url_rule(
            f"{url}/<{pk_type}:res_id>",
            view_func=view_func,
            methods=cls.methods_resource
        )
        app.add_url_rule(
            f"{url}/<{pk_type}:res_id>/<sub_resource>",
            view_func=view_func,
            methods=cls.methods_subresource
        )
        return view_func

    @builder.on_accept()
    def get(self, *args, res_id=None, sub_resource=None, **kwargs):
        if res_id is None:
            return self.on_collection(*args, **kwargs)

        if sub_resource is None:
            return self.on_get(res_id, *args, **kwargs)

        try:
            _sub_resource = getattr(self, f"sub_{sub_resource}")
            return _sub_resource(res_id, *args, **kwargs)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.on_accept()
    def post(self, *args, res_id=None, sub_resource=None, **kwargs):
        if res_id is None:
            return self.on_post(*args, **kwargs)
        try:
            _sub_resource_post = getattr(self, f"sub_{sub_resource}_post")
            return _sub_resource_post(res_id, *args, **kwargs)
        except AttributeError:
            flask.abort(httpcode.NOT_FOUND)

    @builder.no_content
    def delete(self, res_id, *args, **kwargs):
        return self.on_delete(res_id, *args, **kwargs)

    @builder.on_accept()
    def put(self, res_id, *args, **kwargs):
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
