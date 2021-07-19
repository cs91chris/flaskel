from functools import partial

import flask
from webargs import fields, flaskparser

from flaskel import config, httpcode

parser = flaskparser.FlaskParser()
query = partial(parser.use_args, location="query")
payload = partial(parser.use_args, location="json")


class Field:
    integer = partial(fields.Integer)
    string = partial(fields.String)
    decimal = partial(fields.Decimal)
    boolean = partial(fields.Boolean, truthy={"true", 1}, falsy={"false", 0})
    positive = partial(integer, validate=lambda x: x > 0)
    not_negative = partial(integer, validate=lambda x: x >= 0)
    not_positive = partial(integer, validate=lambda x: x <= 0)
    negative = partial(integer, validate=lambda x: x < 0)
    isodate = partial(fields.DateTime, format=config.DATE_ISO_FORMAT)
    list_of = partial(fields.DelimitedList, cls_or_instance=string(), delimiter="+")


class OptField:
    integer = partial(Field.integer, missing=None)
    string = partial(Field.string, missing=None)
    decimal = partial(Field.decimal, missing=None)
    boolean = partial(Field.boolean, missing=False)
    positive = partial(Field.positive, missing=None)
    not_negative = partial(Field.not_negative, missing=None)
    not_positive = partial(Field.not_positive, missing=None)
    negative = partial(Field.negative, missing=None)
    isodate = partial(Field.isodate, missing=None)
    list_of = partial(Field.list_of, missing=())


class ReqField:
    integer = partial(Field.integer, required=True)
    string = partial(Field.string, required=True)
    decimal = partial(Field.decimal, required=True)
    boolean = partial(Field.boolean, required=True)
    positive = partial(Field.positive, required=True)
    not_negative = partial(Field.not_negative, required=True)
    not_positive = partial(Field.not_positive, required=True)
    negative = partial(Field.negative, required=True)
    isodate = partial(Field.isodate, required=True)
    list_of = partial(Field.list_of, required=True)


# noinspection PyUnusedLocal
@parser.error_handler
def handle_error(error, *_, **__):
    flask.abort(httpcode.BAD_REQUEST, response=error.messages)


query_paginate = partial(
    query,
    dict(
        page=OptField.positive(),
        page_size=OptField.positive(),
        related=OptField.boolean(missing=False),
    ),
)


def paginate(f=None):
    @query_paginate()
    def _route(*args, **kwargs):
        params = args[-1]
        if f is None:
            return params

        return f(*args[:-1], params=params, **kwargs)

    return _route if f else _route()
