# create and configure your extensions in this package
# then import your extensions here
from flaskel.ext.celery import celery


EXTENSIONS = {
    # "name": (<extension>, parameters: dict)
    "celery": (celery,),
}
