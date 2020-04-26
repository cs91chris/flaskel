from flask_cors import CORS
from flask_logify import FlaskLogging
from flask_errors_handler import ErrorHandler
from flask_response_builder import ResponseBuilder
from flask_template_support import TemplateSupport
from flask_cloudflare_remote import CloudflareRemote

from .crypto import Argon2

cors = CORS()
argon2 = Argon2()
logger = FlaskLogging()
errors = ErrorHandler()
builder = ResponseBuilder()
template = TemplateSupport()
cfremote = CloudflareRemote()
