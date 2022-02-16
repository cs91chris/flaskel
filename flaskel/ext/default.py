import functools

from flask_cloudflare_remote import CloudflareRemote
from flask_cors import CORS
from flask_errors_handler import ErrorHandler
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_template_support import TemplateSupport

from .caching import Cache
from .crypto.argon import Argon2
from .datetime import FlaskDateHelper
from .errors import ErrorNormalizer
from .healthcheck import HealthCheck
from .jobs import APJobs
from .sqlalchemy import SQLAModel, SQLAlchemy
from .useragent import UserAgent
from .mongo import FlaskMongoDB
from .redis import FlaskRedis
from .sendmail import ClientMail

caching = Cache.caching

cors = CORS()
argon2 = Argon2()
useragent = UserAgent()
logger = FlaskLogging()
builder = ResponseBuilder()
template = TemplateSupport()
cfremote = CloudflareRemote()
health_checks = HealthCheck()
date_helper = FlaskDateHelper()
client_mongo = FlaskMongoDB()
client_redis = FlaskRedis()
client_mail = ClientMail()
error_handler = ErrorHandler(normalizer=ErrorNormalizer())

Scheduler = functools.partial(APJobs)
Database = functools.partial(SQLAlchemy, model_class=SQLAModel)
