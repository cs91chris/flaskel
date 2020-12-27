import functools

from flaskel import cap, httpcode
from flaskel.ext import builder


class HealthCheck:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        """
        self._health_checks = {}

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, bp=None, extensions=()):
        """

        :param app:
        :param bp:
        :param extensions:
        """
        app.config.setdefault('HEALTHCHECK_ABOUT_LINK', None)
        app.config.setdefault('HEALTHCHECK_PATH', '/healthcheck')
        app.config.setdefault('HEALTHCHECK_CONTENT_TYPE', 'application/health+json')

        blueprint = bp or app
        blueprint.add_url_rule(
            app.config['HEALTHCHECK_PATH'],
            view_func=self.do_health_check
        )

        for ex in extensions:
            self.register(**ex)(ex.pop('func'))

    @builder.response('json')
    def do_health_check(self):
        """

        :return:
        """
        healthy = True
        response = dict(
            status='pass',
            checks={},
            links={"about": cap.config['HEALTHCHECK_ABOUT_LINK']}
        )

        for name, check_func in self._health_checks.items():
            try:
                state, message = check_func()
            except Exception as exc:
                state = False
                message = str(exc)

            healthy = state
            response['checks'][name] = dict(
                status='pass' if state else 'fail',
                output=message
            )

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
