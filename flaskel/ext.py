# instantiate flask extension here
#
from flask_logify import FlaskLogging
from flask_errors_handler import ErrorHandler


logger = FlaskLogging()
errors = ErrorHandler()
