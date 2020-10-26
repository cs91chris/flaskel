from flaskel.tasks import celery


@celery.task
def dummy():
    print("DUMMY: test celery worker")
