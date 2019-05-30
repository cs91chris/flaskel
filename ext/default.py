# DO NOT TOUCH this file use you custom module
#
from flask_cors import CORS
from flask_logify import FlaskLogging
from flask_errors_handler import ErrorHandler
from flask_response_builder import ResponseBuilder


cors = CORS()
logger = FlaskLogging()
builder = ResponseBuilder()
errors = ErrorHandler()
