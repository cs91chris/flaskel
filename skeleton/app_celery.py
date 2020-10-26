# noinspection PyUnresolvedReferences
from flaskel.tasks import celery

broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
include = ["tasks"]

broker_transport_options = {
    "socket_timeout": 5,
    "max_retries":    4,
    "interval_start": 0,
    "interval_step":  0.5,
    "interval_max":   3
}

broker_connection_max_retry = 3
