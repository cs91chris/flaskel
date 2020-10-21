from flask_cloudflare_remote import CloudflareRemote
from flask_cors import CORS
from flask_errors_handler import ErrorHandler
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_template_support import TemplateSupport


cors = CORS()
logger = FlaskLogging()
errors = ErrorHandler()
builder = ResponseBuilder()
template = TemplateSupport()
cfremote = CloudflareRemote()
