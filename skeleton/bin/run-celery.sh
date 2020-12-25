#!/bin/bash

celery -A app_celery.celery --config app_celery \
  worker -E -Ofair -P solo -c 2 -l DEBUG
