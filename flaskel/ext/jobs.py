import atexit
import logging
import os

from apscheduler import events
from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.schedulers.blocking import BlockingScheduler
from flask_apscheduler import APScheduler

from flaskel.utils.uuid import get_uuid

try:
    import fcntl
except ImportError:
    fcntl = None


class APJobs(APScheduler):
    def init_app(self, app, test_sync=True):
        app.config.setdefault('SCHEDULER_AUTO_START', False)
        app.config.setdefault('SCHEDULER_PATCH_MULTIPROCESS', True)
        app.config.setdefault('SCHEDULER_LOCK_FILE', '.scheduler.lock')

        if app.config.SCHEDULER_PATCH_MULTIPROCESS is True:
            if fcntl is None:
                app.logger.warning('fcntl not supported on this platform')
            elif not self._set_lock(app.config.SCHEDULER_LOCK_FILE):
                app.logger.info('scheduler already started in another process')
                return  # pragma: no cover

        try:
            super().init_app(app)
        except SchedulerAlreadyRunningError as exc:
            app.logger.exception(exc)
            return

        # if app is in testing mode execute tasks synchronously
        if test_sync and app.testing:
            self._scheduler = BlockingScheduler()

        if app.debug:
            logger = logging.getLogger('apscheduler')
            logger.setLevel(logging.DEBUG)
            logger = logging.getLogger('flask_apscheduler')
            logger.setLevel(logging.DEBUG)

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
        kw['kwargs'] = kwargs
        job_id = get_uuid()
        job = super().add_job(id=job_id, func=func, **kw)
        self.app.logger.debug('added job %s: %s', func, job_id)
        return job

    @staticmethod
    def _set_lock(lock_file):  # pragma: no cover
        """
        ensure that only one worker starts the scheduler
        :return: (boolean) True -> scheduler can start
        """
        f = None

        def unlock():
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
                f.close()
                os.remove(lock_file)
            except OSError:
                pass

        try:
            f = open(lock_file, "wb")
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atexit.register(unlock)
            return True
        except OSError:
            if f is not None:
                try:
                    f.close()
                except OSError:
                    pass
        return False


scheduler = APJobs()


def exception_listener(event):
    logger = scheduler.app.logger
    if event.exception:
        logger.error("An error occurred when executing job: %s", event.job_id)
        logger.exception(event.exception)
        logger.error(event.traceback)
    else:
        logger.debug("successfully executed job: %s", event.job_id)


scheduler.add_listener(
    exception_listener,
    events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR
)
