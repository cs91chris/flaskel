from functools import wraps

import flask
from flask import current_app as cap
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum
from werkzeug.datastructures import Headers

from .builders.builder import Builder
from .config import DEFAULT_BUILDERS, set_default_config


class ResponseBuilder:
    def __init__(self, app=None, builders=None):
        self._builders = {}

        if app is not None:
            self.init_app(app, builders)

    def init_app(self, app, builders=None):
        set_default_config(app)
        app.extensions["response_builder"] = self

        for name, builder in {**DEFAULT_BUILDERS, **(builders or {})}.items():
            self.register_builder(name, builder, **app.config)

    def register_builder(self, name, builder, **kwargs):
        if not issubclass(builder.__class__, Builder):
            raise NameError(
                f"Invalid Builder: '{builder}'. "
                f"You must extend class: '{Builder.__name__}'"
            )

        if not builder.conf:
            builder.conf = kwargs
        else:
            builder.conf.update(kwargs)

        self._builders.update({name: builder})

        def _builder_attr(**params):
            def _wrapper(func=None, data=None):
                """
                func and data are mutual exclusive:
                    if func is present means a decorator builder used
                    if data is provided means decorator used as attribute
                """
                if func is not None:

                    @wraps(func)
                    def wrapped():
                        return self.build_response(name, func(), **params)

                    return wrapped

                return self.build_response(name, data, **params)

            return _wrapper

        setattr(self, name, _builder_attr)

    @staticmethod
    def _empty_response(status, headers):
        resp = flask.make_response(b"", status, headers)
        resp.headers.pop(HeaderEnum.CONTENT_TYPE, None)
        return resp

    def build_response(self, builder=None, data=None, **kwargs):
        if isinstance(builder, str):
            builder = self._builders.get(builder)

        data, status, headers = self.normalize_response_data(data)

        if data is None:
            return self._empty_response(status, headers)

        if not builder:
            default_format = cap.config.get("RB_DEFAULT_RESPONSE_FORMAT")
            m = headers.get(HeaderEnum.CONTENT_TYPE) or default_format
            for value in self._builders.values():
                if value.mimetype == m:
                    builder = value
                    break
            else:
                allowed = ", ".join(self._builders.keys())
                raise NameError(f"Builder not found: using one of: '{allowed}'")
        elif not issubclass(builder.__class__, Builder):
            raise NameError(
                f"Invalid Builder: '{builder}'. "
                f"You must extend class: '{Builder.__name__}'"
            )

        builder.build(data, **kwargs)
        return builder.response(status=status, headers=headers)

    def get_mimetype_accept(self, default=None, acceptable=None, strict=True):
        def find_builder(a):
            for b in self._builders.values():
                if a == b.mimetype:
                    return b
            return None

        mimetypes = flask.request.accept_mimetypes
        default = default or cap.config["RB_DEFAULT_RESPONSE_FORMAT"]
        acceptable = acceptable or cap.config["RB_DEFAULT_ACCEPTABLE_MIMETYPES"]

        if not mimetypes or str(mimetypes) == "*/*":
            builder = find_builder(default)
            if builder:
                return default, builder

        for m in mimetypes:
            m = m[0].split(";")[0]  # in order to remove encoding param
            accept = m if m in acceptable else None
            builder = find_builder(accept)
            if builder:
                return accept, builder

        if strict is True:
            flask.abort(
                httpcode.NOT_ACCEPTABLE,
                f"Not Acceptable: {flask.request.accept_mimetypes}",
            )

        return default, find_builder(default)

    @staticmethod
    def normalize_response_data(data):
        if isinstance(data, tuple):
            v = data + (None,) * (3 - len(data))
            if isinstance(v[1], int):
                return v[0], v[1], Headers(v[2] or {})
            return v[0], v[2], Headers(v[1] or {})
        if isinstance(data, int):
            return None, data, Headers()
        if isinstance(data, flask.Response):
            return data.response, data.status_code, Headers(data.headers)
        return data, None, Headers()

    def no_content(self, func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            resp = func(*args, **kwargs)
            data, status, headers = self.normalize_response_data(resp)

            if data:
                resp = self.build_response(data=resp)
            else:
                status = httpcode.NO_CONTENT if status is None else status
                resp = self._empty_response(status, headers)

            return resp

        return wrapped

    def on_format(self, default=None, acceptable=None):
        def response(fun):
            @wraps(fun)
            def wrapper(*args, **kwargs):
                builder = (
                    flask.request.args.get(cap.config.get("RB_FORMAT_KEY")) or default
                )
                if builder not in (acceptable or self._builders):
                    for k, v in self._builders.items():
                        if v.mimetype == cap.config.get("RB_DEFAULT_RESPONSE_FORMAT"):
                            builder = k
                            break

                return self.build_response(builder, fun(*args, **kwargs))

            return wrapper

        return response

    def on_accept(self, default=None, acceptable=None, strict=True):
        def response(fun):
            @wraps(fun)
            def wrapper(*args, **kwargs):
                _, builder = self.get_mimetype_accept(default, acceptable, strict)
                return self.build_response(builder, fun(*args, **kwargs))

            return wrapper

        return response

    def response(self, builder, **kwargs):
        def _response(f):
            @wraps(f)
            def wrapper(*args, **kw):
                return self.build_response(builder, f(*args, **kw), **kwargs)

            return wrapper

        return _response

    def template_or_json(self, template: str, as_table=False, to_dict=None):
        def response(fun):
            @wraps(fun)
            def wrapper(*args, **kwargs):
                varargs = {}
                builder = self._builders.get("json")

                # check if request is XHR
                if (
                    flask.request.headers.get("X-Requested-With", "").lower()
                    == "xmlhttprequest"
                ):
                    builder = self._builders.get("html")
                    varargs.update(
                        template=template, as_table=as_table, to_dict=to_dict
                    )

                resp = fun(*args, **kwargs)
                return self.build_response(builder, resp, **varargs)

            return wrapper

        return response
