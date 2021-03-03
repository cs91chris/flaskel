import functools

import flask

from flaskel.flaskel import cap, httpcode
from flaskel.ext.default import builder
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

        :param app:
        :param bp:
        :param extensions:
        :param decorators:
        :param executor:
        """
        self._executor = executor or ThreadBatchExecutor
        app.config.setdefault('HEALTHCHECK_ABOUT_LINK', None)
        app.config.setdefault('HEALTHCHECK_PATH', '/healthcheck')
        app.config.setdefault('HEALTHCHECK_PARAM_KEY', 'checks')
        app.config.setdefault('HEALTHCHECK_PARAM_SEP', '+')
        app.config.setdefault('HEALTHCHECK_CONTENT_TYPE', 'application/health+json')

        if not hasattr(app, 'extensions'):
            app.extensions = dict()  # pragma: no cover
        app.extensions['healthcheck'] = self

        view = self.perform
        for decorator in decorators:
            view = decorator(view)

        blueprint = bp or app
        blueprint.add_url_rule(app.config['HEALTHCHECK_PATH'], view_func=view)

        for ex in extensions:
            self.register(**ex)(ex.pop('func'))

    @builder.response('json')
    def perform(self):
        """

        :return:
        """
        healthy = True
        response = dict(
            status='pass', checks={},
            links={"about": cap.config['HEALTHCHECK_ABOUT_LINK']}
        )

        params = flask.request.args.get(cap.config['HEALTHCHECK_PARAM_KEY'])
        all_checks = set(self._health_checks.keys())
        if not params:
            params = all_checks
        else:
            params = params.split(cap.config['HEALTHCHECK_PARAM_SEP'])
            params = set(params).intersection(all_checks)

        # noinspection PyProtectedMember
        app = cap._get_current_object()
        params = list(params)
        tasks = [(self._health_checks.get(p), dict(app=app)) for p in params]
        resp = self._executor(tasks=tasks).run()

        for i, p in enumerate(params):
            state, message = resp[i]
            status = 'pass' if state else 'fail'
            response['checks'][p] = dict(status=status, output=message)
            if not state:
                healthy = False

        if not healthy:
            response['status'] = 'fail'

        status = httpcode.SUCCESS if healthy else httpcode.SERVICE_UNAVAILABLE
        return response, status, {'Content-Type': cap.config['HEALTHCHECK_CONTENT_TYPE']}

    def register(self, name=None, **kwargs):
        """

        :param name:
        :param kwargs:
        :return:
        """

        def _register(func):
            """

            :param func:
            :return:
            """
            nonlocal name
            name = name or func.__name__

            @functools.wraps(func)
            def wrapped():
                self._health_checks[name] = functools.partial(func, **kwargs)

            return wrapped()

        return _register


health_checks = HealthCheck()
