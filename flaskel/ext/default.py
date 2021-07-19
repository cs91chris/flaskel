import functools

from flask_cloudflare_remote import CloudflareRemote
from flask_cors import CORS
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_template_support import TemplateSupport

cors = CORS()
logger = FlaskLogging()
builder = ResponseBuilder()
template = TemplateSupport()
cfremote = CloudflareRemote()

json_builder = functools.partial(builder.on_format("json"))
