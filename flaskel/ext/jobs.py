import logging

from flask_apscheduler import APScheduler
from flaskel.utils.uuid import get_uuid


class APJobs(APScheduler):
    def init_app(self, app):
        super().init_app(app)

        if app.debug:
            logger = logging.getLogger('apscheduler')
            logger.setLevel(logging.DEBUG)
            logger = logging.getLogger('flask_apscheduler')
            logger.setLevel(logging.DEBUG)

        app.config.setdefault('SCHEDULER_AUTO_START', False)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()  # pragma: no cover
        app.extensions['scheduler'] = self

        if app.config.SCHEDULER_AUTO_START is True:
            self.start()

    def add_job(self, func, kwargs=None, **kw):
        """

        :param func:
        :param kwargs:
        :return:
        """
        kwargs = kwargs or {}
        kwargs['app'] = self.app
        kw['kwargs'] = kwargs
        return super().add_job(id=get_uuid(), func=func, **kw)


scheduler = APJobs()
