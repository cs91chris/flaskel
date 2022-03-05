import dataclasses
import typing as t

from flask.views import MethodView, View
from vbcore.http import httpcode, HttpMethod

from flaskel.ext.default import builder
from flaskel.http.exceptions import abort

UrlsType = t.Tuple[t.Union["UrlRule", str], ...]


@dataclasses.dataclass(frozen=True)
class UrlRule:
    url: str
    endpoint: t.Optional[str] = None
    options: t.Optional[dict] = None
    provide_automatic_options: t.Optional[bool] = None


class ViewSupportMixin:
    methods = [
        HttpMethod.GET,
    ]
    default_view_name: str = ""
    default_urls: UrlsType = ()

    @staticmethod
    def not_implemented() -> t.NoReturn:  # pragma: no cover
        abort(httpcode.NOT_IMPLEMENTED)

    @classmethod
    def normalize_url(cls, url: str) -> str:
        return f"/{url.lstrip('/')}"

    @classmethod
    def add_url_rule(
        cls,
        app,
        rule: UrlRule,
        view_func: t.Optional[t.Callable] = None,
    ):
        app.add_url_rule(
            cls.normalize_url(rule.url),
            view_func=view_func,
            methods=cls.methods,
            endpoint=rule.endpoint,
            provide_automatic_options=rule.provide_automatic_options,
            **(rule.options or {}),
        )

    @classmethod
    def prepare_view_func(
        cls,
        name: t.Optional[str] = None,
        view: t.Optional[t.Type["BaseView"]] = None,
        **kwargs,
    ):
        _class = view or cls
        name = name or _class.__name__
        return _class.as_view(name, **kwargs)  # type: ignore

    @classmethod
    def register(
        cls,
        app,
        name: t.Optional[str] = None,
        urls: UrlsType = (),
        view: t.Optional[t.Type["BaseView"]] = None,
        **kwargs,
    ):
        raise NotImplementedError


class BaseView(View, ViewSupportMixin):
    default_view_name: str = "index"
    default_urls: UrlsType = ("/",)

    def dispatch_request(self, *_, **__):
        """
        Must be implemented in every subclass
        """
        return self.not_implemented()  # pragma: no cover

    @classmethod
    def register(
        cls,
        app,
        name: t.Optional[str] = None,
        urls: UrlsType = (),
        view: t.Optional[t.Type["BaseView"]] = None,
        **kwargs,
    ) -> t.Callable:
        """

        :param app: Flask app or blueprint
        :param name: optional view name
        :param urls: optional urls or view name
        :param view: view class, subclass che call this must pass its reference
        :param kwargs: argument passed to cls constructor
        """
        view_func = cls.prepare_view_func(name, view, **kwargs)
        if not urls:
            cls.add_url_rule(app, UrlRule(url=name), view_func)
        for rule in urls:
            _rule = UrlRule(url=rule) if isinstance(rule, str) else rule
            cls.add_url_rule(app, _rule, view_func)
        return view_func


class Resource(MethodView, ViewSupportMixin):
    default_view_name: str = "resource"

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
    def _register_urls(
        cls, app, view_func: t.Callable, url: str, pk_type: str = "int", **kwargs
    ):
        url = cls.normalize_url(url)
        if cls.methods_collection:
            app.add_url_rule(
                url,
                view_func=view_func,
                methods=cls.methods_collection,
                **kwargs,
            )
        if cls.methods_resource:
            app.add_url_rule(
                f"{url}/<{pk_type}:res_id>",
                view_func=view_func,
                methods=cls.methods_resource,
                **kwargs,
            )
        if cls.methods_subresource:
            app.add_url_rule(
                f"{url}/<{pk_type}:res_id>/<sub_resource>",
                view_func=view_func,
                methods=cls.methods_subresource,
                **kwargs,
            )

    @classmethod
    def register(
        cls,
        app,
        name: t.Optional[str] = None,
        urls: UrlsType = (),
        view: t.Optional[t.Type[BaseView]] = None,
        **kwargs,
    ) -> t.Callable:
        view_func = cls.prepare_view_func(name, view, **kwargs)
        pk_type = kwargs.pop("pk_type", "int")  # type of res_id

        if not urls:
            cls._register_urls(app, view_func, name, pk_type)
        for rule in urls:
            if isinstance(rule, str):
                cls._register_urls(app, view_func, rule, pk_type)
            else:
                cls._register_urls(
                    app,
                    view_func,
                    rule.url,
                    pk_type,
                    endpoint=rule.endpoint,
                    provide_automatic_options=rule.provide_automatic_options,
                    **(rule.options or {}),
                )
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
            abort(httpcode.METHOD_NOT_ALLOWED)

        _sub_resource = getattr(self, f"sub_{sub_resource}", None)
        if _sub_resource is None:
            abort(httpcode.NOT_FOUND)
        return _sub_resource(res_id, *args, **kwargs)

    @builder.on_accept()
    def post(self, *args, res_id=None, sub_resource=None, **kwargs):
        if res_id is None:
            return self.on_post(*args, **kwargs)
        if self.methods_subresource and HttpMethod.POST not in self.methods_subresource:
            abort(httpcode.METHOD_NOT_ALLOWED)

        _sub_resource = getattr(self, f"sub_{sub_resource}_post", None)
        if _sub_resource is None:
            abort(httpcode.NOT_FOUND)
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
