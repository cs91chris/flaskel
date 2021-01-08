# Define your extensions in this package and import them here

from flaskel.ext.celery import celery

EXTENSIONS = {
    # "name": (<extension>, parameters: dict)
    "celery": (celery,),
}
