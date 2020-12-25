from celery import Celery


class FlaskCelery:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        :param kwargs:
        """
        self.session = Celery(**kwargs)

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """

        :param app:
        :return:
        """
        if not hasattr(app, 'extensions'):
            app.extensions = {}  # pragma: no cover
        app.extensions['celery'] = self

        self.session.conf.update(app.config.get('CELERY') or {})
        app.logger.debug("Celery configuration\n:{}".format(dict(self.session.conf)))

        class ContextTask(self.session.Task):
            abstract = True

            def __call__(self, *args, **kw):
                with app.app_context():
                    return self.celery.Task.__call__(self, *args, **kw)

        # noinspection PyPropertyAccess
        self.session.Task = ContextTask

    @staticmethod
    def celery_app(app=None, factory=None, conf=None):
        """

        :param app:
        :param factory:
        :param conf:
        :return:
        """
        _app = app or factory.get_or_create(conf)
        _celery = _app.extensions['celery']
        return _celery.session


celery = FlaskCelery()
