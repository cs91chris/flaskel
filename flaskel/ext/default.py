import functools
import typing as t

from flask_cloudflare_remote import CloudflareRemote
from flask_cors import CORS
from flask_errors_handler import ErrorHandler
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_sqlalchemy import SQLAlchemy
from flask_template_support import TemplateSupport

from .caching import Caching
from .crypto.argon import Argon2
from .datetime import FlaskDateHelper
from .errors import ErrorNormalizer
from .healthcheck import HealthCheck
from .jobs import APJobs
from .sendmail import ClientMail
from .sqlalchemy import SQLAModel
from .useragent import UserAgent

cors: CORS = CORS()
logger: FlaskLogging = FlaskLogging()
builder: ResponseBuilder = ResponseBuilder()
template: TemplateSupport = TemplateSupport()
cfremote: CloudflareRemote = CloudflareRemote()
error_handler: ErrorHandler = ErrorHandler(normalizer=ErrorNormalizer())

argon2: Argon2 = Argon2()
caching: Caching = Caching()
useragent: UserAgent = UserAgent()
client_mail: ClientMail = ClientMail()
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
