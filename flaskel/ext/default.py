import functools
import typing as t

from flask_caching import Cache as FlaskCache
from flask_cloudflare_remote import CloudflareRemote
from flask_cors import CORS
from flask_errors_handler import ErrorHandler
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_template_support import TemplateSupport

from . import auth
from .caching import Cache
from .crypto.argon import Argon2
from .datetime import FlaskDateHelper
from .errors import ErrorNormalizer
from .healthcheck import HealthCheck
from .jobs import APJobs
from .mongo import FlaskMongoDB
from .redis import FlaskRedis
from .sendmail import ClientMail
from .sqlalchemy import SQLAModel, SQLAlchemy
from .useragent import UserAgent

caching: FlaskCache = Cache.caching
token_auth: auth.jwt.JWTManager = auth.jwtm

cors: CORS = CORS()
argon2: Argon2 = Argon2()
useragent: UserAgent = UserAgent()
logger: FlaskLogging = FlaskLogging()
builder: ResponseBuilder = ResponseBuilder()
template: TemplateSupport = TemplateSupport()
cfremote: CloudflareRemote = CloudflareRemote()
health_checks: HealthCheck = HealthCheck()
date_helper: FlaskDateHelper = FlaskDateHelper()
client_mongo: FlaskMongoDB = FlaskMongoDB()
client_redis: FlaskRedis = FlaskRedis()
client_mail: ClientMail = ClientMail()
error_handler: ErrorHandler = ErrorHandler(normalizer=ErrorNormalizer())

Scheduler: t.Type[APJobs] = t.cast(
    t.Type[APJobs],
    functools.partial(APJobs),
)

Database: t.Type[SQLAlchemy] = t.cast(
    t.Type[SQLAlchemy],
    functools.partial(SQLAlchemy, model_class=SQLAModel),
)
