from .builder import AppBuilder
from .flaskel import Flaskel, Request, Response, cap, request
from .http.client import (
    FlaskelHttp,
    FlaskelHttpBatch,
    FlaskelHTTPDumper,
    FlaskelJsonRPC,
)
from .http.exceptions import abort
from .standalone import Server
from .tester import TestClient
from .utils import webargs
from .utils.datastruct import ConfigProxy, ExtProxy
from .utils.validator import PayloadValidator
from .version import *  # noqa: F403
from .wsgi import WSGIFactory, BaseApplication


client_redis = ExtProxy("redis")
client_mail = ExtProxy("client_mail")
job_scheduler = ExtProxy("scheduler")
db_session = ExtProxy("sqlalchemy.db.session")
