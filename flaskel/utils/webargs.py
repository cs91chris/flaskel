import functools

import flask
from webargs import fields, flaskparser

from flaskel import config, httpcode

parser = flaskparser.FlaskParser()
query = functools.partial(parser.use_args, location="query")
payload = functools.partial(parser.use_args, location="json")


class Fields:
    integer = fields.Integer
    string = fields.String
    decimal = fields.Decimal
    boolean = functools.partial(fields.Boolean, truthy={'true', 1}, falsy={'false', 0})
    positive = functools.partial(fields.Integer, validate=lambda x: x > 0)
    not_negative = functools.partial(fields.Integer, validate=lambda x: x >= 0)
    not_positive = functools.partial(fields.Integer, validate=lambda x: x <= 0)
    negative = functools.partial(fields.Integer, validate=lambda x: x < 0)
    isodate = functools.partial(fields.DateTime, format=config.DATE_ISO_FORMAT)

    @classmethod
    def list_of(cls, elem_field=None, delimiter='+', **kwargs):
        return fields.DelimitedList(elem_field or cls.string, delimiter=delimiter, **kwargs)


# noinspection PyUnusedLocal
@parser.error_handler
def handle_error(error, *args, **kwargs):
    flask.abort(httpcode.BAD_REQUEST, response=error.messages)
