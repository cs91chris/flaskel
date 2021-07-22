import functools

import flask

from flaskel.ext.default import builder
from flaskel.flaskel import cap
from flaskel.flaskel import httpcode
from flaskel.utils.batch import BatchExecutor
from flaskel.utils.batch import ThreadBatchExecutor


class HealthCheck:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        """
        self._executor = None
        self._health_checks = {}

        if app:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(self, app, bp=None, extensions=(), decorators=(), executor=None):
        """

        :param app: Flask app or blueprint instance
        :param bp: optional a blueprint instance on which register the healthcheck view
        :param extensions: functions and arguments that execute the checks
        :param decorators: functions that decorates the healthcheck view
        :param executor: batch executor class, must be subclass of BatchExecutor
        """
        self._executor = executor or ThreadBatchExecutor
        assert issubclass(self._executor, BatchExecutor)

        self.set_default_config(app)
        self.register_route(bp or app, decorators)
        self.register_extensions(app, extensions)

        if not hasattr(app, "extensions"):
            app.extensions = dict()  # pragma: no cover
        app.extensions["healthcheck"] = self

    @staticmethod
    def set_default_config(app):
        app.config.setdefault("HEALTHCHECK_ABOUT_LINK", None)
        app.config.setdefault("HEALTHCHECK_VIEW_NAME", "healthcheck")
        app.config.setdefault("HEALTHCHECK_PATH", "/healthcheck")
        app.config.setdefault("HEALTHCHECK_PARAM_KEY", "checks")
        app.config.setdefault("HEALTHCHECK_PARAM_SEP", "+")
        app.config.setdefault("HEALTHCHECK_CONTENT_TYPE", "application/health+json")

    def register_route(self, app, decorators=()):
        """

        :param app: Flask app or blueprint instance
        :param decorators: functions that decorates the healthcheck view
        """
        view = self.perform
        for decorator in decorators:
            view = decorator(view)

        conf = cap.config
        app.add_url_rule(
            conf["HEALTHCHECK_PATH"], conf["HEALTHCHECK_VIEW_NAME"], view_func=view
        )

    def register_extensions(self, app, extensions):
        """

        :param app: Flask app instance
        :param extensions: functions and arguments that execute the checks
        """
        for ex in extensions:
            try:
                func = ex.pop("func")
                self.register(**ex)(func)
            except Exception as exc:  # pylint: disable=W0703
                app.logger.exception(exc)
                app.logger.error("invalid healthcheck extension: %s", ex)

    @builder.response("json")
    def perform(self):
        healthy = True
        response = dict(
            status="pass",
            checks={},
            links={"about": cap.config["HEALTHCHECK_ABOUT_LINK"]},
        )

        params = flask.request.args.get(cap.config["HEALTHCHECK_PARAM_KEY"])
        all_checks = set(self._health_checks.keys())
        if not params:
            params = all_checks
        else:
            params = params.split(cap.config["HEALTHCHECK_PARAM_SEP"])
            params = set(params).intersection(all_checks)

        # noinspection PyProtectedMember,PyUnresolvedReferences
        app = cap._get_current_object()  # pylint: disable=W0212
        params = list(params)
        tasks = [(self._health_checks.get(p), dict(app=app)) for p in params]
        resp = self._executor(tasks=tasks).run()

        for i, p in enumerate(params):
            state, message = resp[i]
            status = "pass" if state else "fail"
            response["checks"][p] = dict(status=status, output=message)
            if not state:
                healthy = False

        if not healthy:
            response["status"] = "fail"

        status = httpcode.SUCCESS if healthy else httpcode.SERVICE_UNAVAILABLE
        return (
            response,
            status,
            {"Content-Type": cap.config["HEALTHCHECK_CONTENT_TYPE"]},
        )

    def register(self, name=None, **kwargs):  # pylint: disable=W0613
        """

        :param name:
        :return:
        """

        def _register(func):
            nonlocal name
            name = name or func.__name__

            @functools.wraps(func)
            def wrapped():
                self._health_checks[name] = functools.partial(func, **kwargs)

            return wrapped()

        return _register


health_checks = HealthCheck()
