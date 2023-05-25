import os.path
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from apscheduler import events
from vbcore.tester.asserter import Asserter

from flaskel.ext.default import Scheduler
from flaskel.ext.jobs import undefined


def test_init_app(flaskel_app):
    flaskel_app.config.SCHEDULER_AUTO_START = True
    scheduler = Scheduler()

    scheduler.start = MagicMock()
    scheduler.set_lock = MagicMock()
    scheduler.set_lock.return_value = True

    scheduler.init_app(flaskel_app)
    Asserter.assert_equals(flaskel_app.extensions["scheduler"], scheduler)


@patch("flaskel.ext.jobs.get_uuid")
def test_add(mock_get_uuid, flaskel_app):
    mock_get_uuid.side_effect = lambda: "job-id"
    flaskel_app.config.SCHEDULER_AUTO_START = True
    scheduler = Scheduler()
    scheduler.add_job = MagicMock()
    scheduler.set_lock = MagicMock()
    scheduler.set_lock.return_value = True

    scheduler.init_app(flaskel_app)
    scheduler.add("test_function")
    scheduler.add_job.assert_called_once_with(
        id="job-id",
        func="test_function",
        trigger=None,
        args=None,
        kwargs=None,
        name=None,
        misfire_grace_time=undefined,
        coalesce=undefined,
        max_instances=undefined,
        next_run_time=undefined,
        jobstore="default",
        executor="default",
        replace_existing=False,
    )


def test_set_lock(tmpdir):
    lock_file = tmpdir.join("test_set_lock.lock")
    scheduler = Scheduler()
    Asserter.assert_true(scheduler.set_lock(lock_file))
    Asserter.assert_true(os.path.isfile(lock_file.strpath))


@pytest.mark.parametrize(
    "event, level, message",
    [
        (
            events.SchedulerEvent(code=events.EVENT_SCHEDULER_STARTED),
            "DEBUG",
            "received event: <SchedulerEvent (code=1)>",
        ),
        (
            events.JobExecutionEvent(
                code=events.EVENT_JOB_ERROR,
                job_id="test-job",
                jobstore="default",
                scheduled_run_time=datetime.now(),
                exception=ValueError("value-error"),
            ),
            "ERROR",
            "An error occurred when executing job: test-job",
        ),
        (
            events.JobExecutionEvent(
                events.EVENT_JOB_EXECUTED,
                job_id="test-job",
                jobstore="default",
                scheduled_run_time=datetime.now(),
            ),
            "DEBUG",
            "successfully executed job: test-job, returned value: None",
        ),
        (
            events.JobSubmissionEvent(
                events.EVENT_JOB_ADDED,
                job_id="test-job",
                jobstore="default",
                scheduled_run_times=[datetime.now()],
            ),
            "INFO",
            "successfully added job: test-job",
        ),
    ],
    ids=[
        "EVENT_SCHEDULER_STARTED",
        "EVENT_JOB_ERROR",
        "EVENT_JOB_EXECUTED",
        "EVENT_JOB_ADDED",
    ],
)
def test_exception_listener(event, level, message, flaskel_app, caplog):
    scheduler = Scheduler()
    scheduler.app = flaskel_app

    scheduler.exception_listener(event)
    Asserter.assert_equals(caplog.records[0].levelname, level)
    Asserter.assert_equals(caplog.records[0].getMessage(), message)
