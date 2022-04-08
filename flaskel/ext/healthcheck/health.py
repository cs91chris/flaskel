import enum
import typing as t
from functools import partial, wraps

from flask import Blueprint
from vbcore.batch import BatchExecutor
from vbcore.datastruct import LStrEnum
from vbcore.http import httpcode, HttpMethod
from vbcore.http.headers import ContentTypeEnum, HeaderEnum

from flaskel.flaskel import Flaskel, request

from .checkers import CheckerResponseType

DecoratorType = t.Callable[[t.Callable], None]
ExecutorType = t.TypeVar("ExecutorType", bound=BatchExecutor)
CheckerType = t.Tuple[t.Callable, t.Optional[t.Dict[str, t.Any]]]


class CheckStatus(LStrEnum):
    FAIL = enum.auto()
    PASS = enum.auto()
    WARN = enum.auto()


class HealthCheck:
    def __init__(self, app: t.Optional[Flaskel] = None, **kwargs):
        self._executor = BatchExecutor
        self._checkers: t.Dict[str, t.Callable] = {}
        self.app: t.Optional[Flaskel] = t.cast(Flaskel, None)

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(
        self,
        app: Flaskel,
        blueprint: t.Optional[Blueprint] = None,
        checkers: t.Tuple[CheckerType, ...] = (),
        decorators: t.Tuple[DecoratorType, ...] = (),
        executor: t.Optional[ExecutorType] = None,
    ):
        """

        :param app: Flaskel instance
        :param blueprint: optional a blueprint instance on which register the healthcheck view
        :param checkers: functions with arguments that execute the checks
        :param decorators: functions that decorates the healthcheck view
        :param executor: batch executor class, must be subclass of BatchExecutor
        """
        self.app = app
        self._executor = executor or self._executor

        self.set_default_config()
        self.register_checkers(checkers)
        self.register_route(blueprint or app, decorators)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["healthcheck"] = self

    def set_default_config(self):
        self.app.config.setdefault("HEALTHCHECK_ABOUT_LINK", None)
        self.app.config.setdefault("HEALTHCHECK_VIEW_NAME", "healthcheck")
        self.app.config.setdefault("HEALTHCHECK_PATH", "/healthcheck")
        self.app.config.setdefault("HEALTHCHECK_PARAM_KEY", "checks")
        self.app.config.setdefault("HEALTHCHECK_PARAM_SEP", "+")
        self.app.config.setdefault(
            "HEALTHCHECK_CONTENT_TYPE", ContentTypeEnum.JSON_HEALTH
        )

    def register_route(
        self,
        blueprint: t.Optional[t.Union[Flaskel, Blueprint]] = None,
        decorators: t.Tuple[DecoratorType, ...] = (),
    ) -> t.Callable:
        view = self.perform
        for decorator in decorators:
            view = decorator(view)

        blueprint.add_url_rule(
            self.app.config.HEALTHCHECK_PATH,
            self.app.config.HEALTHCHECK_VIEW_NAME,
            methods=[HttpMethod.GET],
            view_func=view,
        )
        return view

    def register_checkers(self, checkers: t.Tuple[CheckerType, ...]):
        for func, kwargs in checkers:
            self.register(**(kwargs or {}))(func)

    def get_checkers(self) -> t.List[str]:
        params = request.args.get(self.app.config.HEALTHCHECK_PARAM_KEY)
        only_checkers = (
            params.split(self.app.config.HEALTHCHECK_PARAM_SEP) if params else None
        )
        all_checkers = set(self._checkers)
        return list(
            all_checkers
            if not only_checkers
            else set(only_checkers).intersection(all_checkers)
        )

    def execute(self) -> t.Tuple[t.List[str], t.List[CheckerResponseType]]:
        checkers = self.get_checkers()
        tasks = [(self._checkers.get(c), dict(app=self.app)) for c in checkers]
        return checkers, self._executor(tasks=tasks).run()

    def perform(self) -> t.Tuple[dict, int, dict]:
        healthy = True
        response: t.Dict[str, t.Any] = {
            "status": CheckStatus.PASS,
            "checks": {},
            "links": {"about": self.app.config.HEALTHCHECK_ABOUT_LINK},
        }

        checkers, checkers_responses = self.execute()
        for index, name in enumerate(checkers):
            state, message = checkers_responses[index]
            status = CheckStatus.PASS if state else CheckStatus.FAIL
            response["checks"][name] = {"status": status, "output": message}
            if not state:
                healthy = False

        if not healthy:
            response["status"] = CheckStatus.FAIL

        return (
            response,
            httpcode.SUCCESS if healthy else httpcode.MULTI_STATUS,
            {HeaderEnum.CONTENT_TYPE: self.app.config.HEALTHCHECK_CONTENT_TYPE},
        )

    def register(self, name: t.Optional[str] = None, **kwargs):
        def decorator(func):
            @wraps(func)
            def wrapped():
                self._checkers[name or func.__name__] = partial(func, **kwargs)

            return wrapped()

        return decorator
