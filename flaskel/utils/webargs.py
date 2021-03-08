from functools import partial

import flask
from webargs import fields, flaskparser

from flaskel import config, httpcode

parser = flaskparser.FlaskParser()
query = partial(parser.use_args, location="query")
payload = partial(parser.use_args, location="json")


class Fields:
    integer = partial(fields.Integer, missing=None)
    string = partial(fields.String, missing=None)
    decimal = partial(fields.Decimal, missing=None)
    boolean = partial(fields.Boolean, missing=None, truthy={'true', 1}, falsy={'false', 0})
    positive = partial(fields.Integer, missing=None, validate=lambda x: x > 0)
    not_negative = partial(fields.Integer, missing=None, validate=lambda x: x >= 0)
    not_positive = partial(fields.Integer, missing=None, validate=lambda x: x <= 0)
    negative = partial(fields.Integer, missing=None, validate=lambda x: x < 0)
    isodate = partial(fields.DateTime, missing=None, format=config.DATE_ISO_FORMAT)
    list_of = partial(fields.DelimitedList, missing=(), cls_or_instance=string, delimiter='+')


# noinspection PyUnusedLocal
@parser.error_handler
def handle_error(error, *args, **kwargs):
    flask.abort(httpcode.BAD_REQUEST, response=error.messages)


def paginate(f=None):
    @query(dict(
        page=Fields.positive(),
        page_size=Fields.positive(),
        related=Fields.boolean(missing=False),
    ))
    def _route(*args, **kwargs):
        params = args[-1]
        if f is None:
            return params

        return f(*args[:-1], params=params, **kwargs)

    return _route if f else _route()
