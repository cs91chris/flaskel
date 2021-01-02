import functools

import flask
from webargs import flaskparser

from flaskel import httpcode

parser = flaskparser.FlaskParser()
query = functools.partial(parser.use_args, location="query")
payload = functools.partial(parser.use_args, location="json")


# noinspection PyUnusedLocal
@parser.error_handler
def handle_error(error, *args, **kwargs):
    flask.abort(httpcode.BAD_REQUEST, response=error.messages)
