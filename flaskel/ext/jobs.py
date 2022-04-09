import atexit
import datetime
import logging
import os
import typing as t
from threading import Lock

from vbcore.uuid import get_uuid

try:
    from apscheduler import events
    from apscheduler.schedulers import SchedulerAlreadyRunningError
    from apscheduler.util import undefined
    from flask_apscheduler import APScheduler
except ImportError:  # pragma: no cover
    events = undefined = None
    SchedulerAlreadyRunningError = Exception
    BlockingScheduler = APScheduler = object

try:
    import fcntl

    THREAD_LOCK = Lock()
except ImportError:  # pragma: no cover
    THREAD_LOCK = fcntl = None  # type: ignore


class APJobs(APScheduler):
    def init_app(self, app):
        # this is necessary because super().init_app is conditionally invoked
        self.app = app

        if APScheduler is object:
            raise ImportError(
                "you must install 'flask_apscheduler'"
            )  # pragma: no cover

        self.set_config(app)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["scheduler"] = self

        if app.config.SCHEDULER_PATCH_MULTITHREAD is True:
            if fcntl is None:  # pragma: no cover
                app.logger.warning(
                    "fcntl not supported on this platform, no locking mechanism used"
                )
            elif not self.set_lock(app.config.SCHEDULER_LOCK_FILE):
                app.logger.info("scheduler already started in another process")
                return

        if not self.running and app.config.SCHEDULER_AUTO_START is True:
            try:
                super().init_app(app)
                self.add_listener(self.exception_listener, events.EVENT_ALL)
                self.start()
            except SchedulerAlreadyRunningError as exc:  # pylint: disable=broad-except
                app.logger.exception(exc)

    @staticmethod
    def set_config(app):
        app.config.setdefault("SCHEDULER_AUTO_START", False)
        app.config.setdefault("SCHEDULER_PATCH_MULTITHREAD", True)
        app.config.setdefault("SCHEDULER_LOCK_FILE", ".scheduler.lock")

        if app.debug:
            logger = logging.getLogger("apscheduler")
            logger.setLevel(logging.DEBUG)
            logger = logging.getLogger("flask_apscheduler")
            logger.setLevel(logging.DEBUG)

    # pylint: disable=too-many-arguments
    def add(
        self,
        func: t.Optional[t.Union[str, t.Callable]],
        trigger: t.Optional[t.Union[str, t.Callable]] = None,
        args: t.Optional[tuple] = None,
        kwargs: t.Optional[t.Dict[str, t.Any]] = None,
        name: t.Optional[str] = None,
        misfire_grace_time: int = undefined,
        coalesce: bool = undefined,
        max_instances: int = undefined,
        next_run_time: t.Optional[datetime.datetime] = undefined,
        jobstore: str = "default",
        executor: str = "default",
        replace_existing: bool = False,
        **kw,
    ):
        if not self.running:
            self.app.logger.warning(
                "scheduler not running or not started in this process"
            )

        job = self.add_job(
            id=get_uuid(),
            func=func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            name=name,
            misfire_grace_time=misfire_grace_time,
            coalesce=coalesce,
            max_instances=max_instances,
            next_run_time=next_run_time,
            jobstore=jobstore,
            executor=executor,
            replace_existing=replace_existing,
            **kw,
        )
        self.app.logger.debug("added job %s: %s", func, job.id)
        return job

    def set_lock(self, lock_file: str) -> bool:
        """
        ensure that only one worker starts the scheduler
        :return: (boolean) True -> scheduler can start
        """
        file = None

        def unlock():
            fcntl.flock(file, fcntl.LOCK_UN)
            file.close()
            os.remove(lock_file)

        try:
            with THREAD_LOCK:
                # pylint: disable=consider-using-with
                file = open(lock_file, "w", encoding="utf-8")
                file.write(str(os.getpid()))
                file.flush()
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                atexit.register(unlock)
            return True
        except OSError as exc:
            self.app.logger.exception(exc)
            return False

    def exception_listener(self, event: "events.JobExecutionEvent"):
        code = event.code
        logger = self.app.logger
        if code == events.EVENT_JOB_ERROR:
            logger.error("An error occurred when executing job: %s", event.job_id)
            if isinstance(event, events.JobExecutionEvent):
                logger.exception(event.exception)
                logger.error(event.traceback)
        elif code == events.EVENT_JOB_ADDED:
            logger.info("successfully added job: %s", event.job_id)
        elif code == events.EVENT_JOB_EXECUTED:
            logger.debug(
                "successfully executed job: %s, returned value: %s",
                event.job_id,
                event.retval,
            )
        elif isinstance(event, events.JobEvent):
            logger.debug("received event (%s) for job: %s", event, event.job_id)
        else:
            logger.debug("received event: %s", event)
