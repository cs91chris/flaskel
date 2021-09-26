import typing as t

import flask
from flask.views import MethodView, View

from flaskel import httpcode, HttpMethod
from flaskel.ext.default import builder

DefaultUrlsType = t.Tuple[t.Union[t.Dict[str, str], str], ...]


class ViewSupportMixin:
    default_view_name: str = None
    default_urls: DefaultUrlsType = ()

    @staticmethod
    def normalize_url(url):
        return f"/{url.lstrip('/')}"

    @staticmethod
    def not_implemented():  # pragma: no cover
        flask.abort(httpcode.NOT_IMPLEMENTED)

    @classmethod
    def register(cls, app, name=None, urls=(), **kwargs):
        raise NotImplementedError


class BaseView(View, ViewSupportMixin):
    methods = [
        HttpMethod.GET,
    ]
    default_view_name: str = "index"
    default_urls: DefaultUrlsType = ("/",)

    def dispatch_request(self, *_, **__):
        """
        Must be implemented in every subclass
        """
        return self.not_implemented()  # pragma: no cover

    @classmethod
    def register(cls, app, name=None, urls=(), **kwargs):
        """

        :param app: Flask app or blueprint
        :param name: optional view name
        :param urls: optional urls or view name
        :param kwargs: argument passed to cls constructor
        """
        name = name or cls.__name__
        view = cls.as_view(name, **kwargs)
        for u in urls or (f"/{name}",):
            if isinstance(u, dict):
                url = u.pop("url")
                app.add_url_rule(url, view_func=view, methods=cls.methods, **u)
            else:
                app.add_url_rule(u, view_func=view, methods=cls.methods)
        return view


class Resource(MethodView, ViewSupportMixin):
    default_view_name: str = "resource"
    default_urls: DefaultUrlsType = ()

    methods_collection = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]
    methods_subresource = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]
    methods_resource = [
        HttpMethod.GET,
        HttpMethod.PUT,
        HttpMethod.DELETE,
    ]

    @classmethod
    def _register_urls(cls, app, view_func, pk_type, url):
        url = cls.normalize_url(url)
        if cls.methods_collection:
            app.add_url_rule(url, view_func=view_func, methods=cls.methods_collection)
        if cls.methods_resource:
            app.add_url_rule(
                f"{url}/<{pk_type}:res_id>",
                view_func=view_func,
                methods=cls.methods_resource,
            )
        if cls.methods_subresource:
            app.add_url_rule(
                f"{url}/<{pk_type}:res_id>/<sub_resource>",
                view_func=view_func,
                methods=cls.methods_subresource,
            )

    @classmethod
    def register(cls, app, name=None, urls=(), view=None, pk_type="int", **kwargs):
        """

        :param app: Flask or Blueprint instance
        :param name: view name
        :param urls: url to bind if missing, name is used
        :param view: view class, subclass che call this must pass its reference
        :param pk_type: type of res_id
        """
        _class = view or cls
        name = name or _class.__name__
        view_func = _class.as_view(name, **kwargs)
        for url in urls or (name,):
            cls._register_urls(app, view_func, pk_type, url)
        return view_func

    @builder.no_content
    def head(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    @builder.on_accept()
    def get(self, *args, res_id=None, sub_resource=None, **kwargs):
        if res_id is None:
            return self.on_collection(*args, **kwargs)
        if sub_resource is None:
            return self.on_get(res_id, *args, **kwargs)
        if self.methods_subresource and HttpMethod.GET not in self.methods_subresource:
            flask.abort(httpcode.METHOD_NOT_ALLOWED)

        _sub_resource = getattr(self, f"sub_{sub_resource}", None)
        if _sub_resource is None:
            flask.abort(httpcode.NOT_FOUND)
        return _sub_resource(res_id, *args, **kwargs)

    @builder.on_accept()
    def post(self, *args, res_id=None, sub_resource=None, **kwargs):
        if res_id is None:
            return self.on_post(*args, **kwargs)
        if self.methods_subresource and HttpMethod.POST not in self.methods_subresource:
            flask.abort(httpcode.METHOD_NOT_ALLOWED)

        _sub_resource = getattr(self, f"sub_{sub_resource}_post", None)
        if _sub_resource is None:
            flask.abort(httpcode.NOT_FOUND)
        return _sub_resource(res_id, *args, **kwargs)

    @builder.no_content
    def delete(self, res_id, *args, **kwargs):
        return self.on_delete(res_id, *args, **kwargs)

    @builder.on_accept()
    def put(self, *args, res_id=None, **kwargs):
        return self.on_put(*args, res_id=res_id, **kwargs)

    def on_get(self, *_, **__):
        return self.not_implemented()  # pragma: no cover

    def on_post(self, *_, **__):
        return self.not_implemented()  # pragma: no cover

    def on_put(self, *_, **__):
        return self.not_implemented()  # pragma: no cover

    def on_delete(self, *_, **__):
        return self.not_implemented()  # pragma: no cover

    def on_collection(self, *_, **__):
        return self.not_implemented()  # pragma: no cover
