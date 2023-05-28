import functools
import typing as t

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from .caching import Caching
from .cloudflare.remote import CloudflareRemote
from .crypto.argon import Argon2
from .datetime import FlaskDateHelper
from .errors.handler import ErrorHandler
from .healthcheck import HealthCheck
from .jobs import APJobs
from .logging.logging import FlaskLogging
from .response.builder import ResponseBuilder
from .sqlalchemy import SQLAModel
from .templating.support import TemplateSupport
from .useragent import UserAgent

cors: CORS = CORS()
logger: FlaskLogging = FlaskLogging()
builder: ResponseBuilder = ResponseBuilder()
template: TemplateSupport = TemplateSupport()
cfremote: CloudflareRemote = CloudflareRemote()
error_handler: ErrorHandler = ErrorHandler()

argon2: Argon2 = Argon2()
caching: Caching = Caching()
useragent: UserAgent = UserAgent()
health_checks: HealthCheck = HealthCheck()
date_helper: FlaskDateHelper = FlaskDateHelper()

Scheduler: t.Type[APJobs] = t.cast(
    t.Type[APJobs],
    functools.partial(APJobs),
)

Database: t.Type[SQLAlchemy] = t.cast(
    t.Type[SQLAlchemy],
    functools.partial(SQLAlchemy, model_class=SQLAModel),
)
