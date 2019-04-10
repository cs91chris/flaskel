# DO NOT TOUCH this file use you custom module
#
from flask_logify import FlaskLogging
from flask_errors_handler import ErrorHandler
from flask_cors import CORS


cors = CORS()
logger = FlaskLogging()
errors = ErrorHandler()
