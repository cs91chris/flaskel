from functools import wraps

import flask
from flask import current_app as cap
from jinja2 import TemplateError
from werkzeug.exceptions import default_exceptions

from .dispatchers import DEFAULT_DISPATCHERS, ErrorDispatcher
from .exception import ApiProblem
from .normalize import BaseNormalize, ErrorNormalizer


class ErrorHandler:
    def __init__(self, app=None, **kwargs):
        """

        :param app: optional Flask instance
        """
        self._response = kwargs.get("response")
        self._exc_class = kwargs.get("exc_class")
        self._normalizer = kwargs.get("normalizer")

        if app is not None:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(
        self,
        app,
        response=None,
        exc_class=None,
        dispatcher=None,
        handler=None,
        normalizer=None,
    ):
        """

        :param app: Flask instance
        :param response: decorator that produces a Flask Response object
        :param exc_class: subclass of ApiProblem
        :param dispatcher: ErrorDispatcher instance or default configured string name
        :param handler: app error handler one of (api, web)
        :param normalizer: normalize exceptions class
        """
        self._exc_class = exc_class or self._exc_class or ApiProblem
        self._normalizer = normalizer or self._normalizer or ErrorNormalizer()
        self._response = response or self._response or self._default_response_builder

        assert issubclass(self._exc_class, ApiProblem)
        assert isinstance(self._normalizer, BaseNormalize)

        self.set_default_config(app)

        if not hasattr(app, "extensions"):
            app.extensions = dict()  # pragma: no cover
        app.extensions["errors_handler"] = self

        dispatcher = dispatcher or app.config["ERROR_DISPATCHER"]
        if dispatcher is not None:
            self.register_dispatcher(app, dispatcher)

        handler = handler or app.config["ERROR_HANDLER"]
        if handler == "api":
            self.api_register(app)  # pragma: no cover
        elif handler == "web":
            self.web_register(app)  # pragma: no cover
        else:
            app.logger.warning("invalid handler: '%s'", handler)

    @staticmethod
    def set_default_config(app):
        """

        :param app: Flask instance
        """
        app.config.setdefault("ERROR_PAGE", "error.html")
        app.config.setdefault("ERROR_XHR_ENABLED", True)
        app.config.setdefault("ERROR_DEFAULT_MSG", "Unhandled Exception")
        app.config.setdefault("ERROR_FORCE_CONTENT_TYPE", True)
        app.config.setdefault("ERROR_CONTENT_TYPES", ("json", "xml"))
        app.config.setdefault("ERROR_DISPATCHER", None)
        app.config.setdefault("ERROR_HANDLER", None)

    def _default_response_builder(self, f):
        """

        :param f: function that returns dict response, status code and headers dict
        :return: flask response of decorated function
        """

        @wraps(f)
        def wrapper(*args, **kwargs):
            r, s, h = f(*args, **kwargs)

            if not h.get("Content-Type"):
                h["Content-Type"] = "application/{}+json".format(self._exc_class.ct_id)
            elif cap.config["ERROR_FORCE_CONTENT_TYPE"] is True:
                h = self._force_content_type(h)

            options = dict(status=s, headers=h, mimetype=h["Content-Type"])
            return flask.Response(flask.json.dumps(r), **options)

        return wrapper

    def _force_content_type(self, hdr):
        """

        :param hdr: headers dict
        :return: updated headers
        """
        ct_id = self._exc_class.ct_id
        ct = hdr.get("Content-Type") or "x-application/{}".format(ct_id)

        if ct_id not in ct:
            if any([i in ct for i in cap.config["ERROR_CONTENT_TYPES"]]):
                ct = "/{}+".format(ct_id).join(ct.split("/", maxsplit=1))

        hdr.update({"Content-Type": ct})
        return hdr

    @staticmethod
    def register(*bps, code=None):
        """

        :param bps: blueprint's list or flask app
        :param code: optional a specific http code otherwise all
        """

        def _register(hderr):
            """

            :param hderr: function that takes only an Exception object as argument
            """

            @wraps(hderr)
            def wrapper():
                for b in bps:
                    if code is not None:
                        b.errorhandler(code)(hderr)
                    else:
                        for c in default_exceptions.keys():
                            b.errorhandler(c)(hderr)

                        ErrorHandler.failure(b)(hderr)

            return wrapper()

        return _register

    @staticmethod
    def failure(bp):
        """

        :param bp: blueprint or flask app
        """

        def _register(hderr):
            """

            :param hderr: function that takes only an Exception object as argument
            """

            @wraps(hderr)
            def wrapper():
                bp.register_error_handler(Exception, hderr)

            return wrapper()

        return _register

    def _failure_handler(self, ex):
        """

        :param ex: Exception instance
        :return: default template rendered response
        """
        ex = self._normalizer.normalize(ex, self._exc_class)
        return flask.render_template_string(ex.default_html_template, exc=ex), ex.code

    def _api_handler(self, ex):
        """

        :param ex: Exception instance
        :return: response built from self._response
        """
        ex = self._normalizer.normalize(ex, self._exc_class)

        if isinstance(ex.response, flask.Response):
            return ex.response, ex.code

        resp = self._response(lambda: ex.prepare_response())()

        if cap.config["ERROR_FORCE_CONTENT_TYPE"] is True:
            resp.headers = self._force_content_type(resp.headers)

        return resp

    def _web_handler(self, ex):
        """

        :param ex: Exception instance
        :return: a template rendered response
        """
        ex = self._normalizer.normalize(ex, self._exc_class)

        if cap.config["ERROR_XHR_ENABLED"] is True:
            # check if request is XHR (for compatibility with old clients)
            if (
                flask.request.headers.get("X-Requested-With", "").lower()
                == "xmlhttprequest"
            ):
                return self._api_handler(ex)

        try:
            return flask.render_template(cap.config["ERROR_PAGE"], error=ex), ex.code
        except TemplateError:
            return (
                flask.render_template_string(ex.default_html_template, exc=ex),
                ex.code,
            )

    def default_register(self, *bps):
        """

        :param bps:
        """
        for b in bps:
            ErrorHandler.register(b)(self._failure_handler)

    def failure_register(self, *bps, callback=None):
        """

        :param bps: blueprint or flask app
        :param callback: optional function to register
        """
        for b in bps:
            ErrorHandler.failure(b)(callback or self._failure_handler)

    def api_register(self, *bps, callback=None, **kwargs):
        """

        :param bps: app or blueprint
        :param callback: optional function to register
        :param kwargs: passed to register
        """
        for b in bps:
            ErrorHandler.register(b, **kwargs)(callback or self._api_handler)

    def web_register(self, *bps, callback=None, **kwargs):
        """

        :param bps: app or blueprint
        :param callback: optional function to register
        :param kwargs: passed to register
        """
        for b in bps:
            ErrorHandler.register(b, **kwargs)(callback or self._web_handler)

    def register_dispatcher(self, app, dispatcher, codes=(404, 405)):
        """

        :param app: Flask instance
        :param dispatcher: ErrorDispatcher class or a string name of default dispatcher
        :param codes: list of http codes
        """
        try:
            if issubclass(dispatcher, ErrorDispatcher):
                dispatcher_class = dispatcher
            else:  # pragma: no cover
                app.logger.error(
                    "dispatcher '%s' must be subclass of '%s'",
                    dispatcher,
                    ErrorDispatcher.__name__,
                )
                return
        except TypeError:  # dispatcher is not a class
            dispatcher_class = DEFAULT_DISPATCHERS.get(dispatcher)
            if not dispatcher_class:  # pragma: no cover
                app.logger.error(
                    "dispatcher '%s' not exists. Use one of %s",
                    dispatcher,
                    DEFAULT_DISPATCHERS.keys(),
                )
                return

        for c in codes:

            @app.errorhandler(c)
            def error_handler(exc):
                """

                :param exc: Exception instance
                :return: dispatcher response
                """
                d = dispatcher_class()
                return d.dispatch(self._normalizer.normalize(exc, self._exc_class))
