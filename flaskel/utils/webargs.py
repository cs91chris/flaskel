from functools import partial

import flask
from webargs import fields, flaskparser

from flaskel import httpcode

parser = flaskparser.FlaskParser()
query = partial(parser.use_args, location="query")
payload = partial(parser.use_args, location="json")


class Field:
    integer = partial(fields.Integer)
    string = partial(fields.String)
    decimal = partial(fields.Decimal)
    boolean = partial(fields.Boolean, truthy={"true", 1}, falsy={"false", 0})
    positive = partial(integer, validate=lambda x: x > 0)
    negative = partial(integer, validate=lambda x: x < 0)
    not_positive = partial(integer, validate=lambda x: x <= 0)
    not_negative = partial(integer, validate=lambda x: x >= 0)
    isodate = partial(fields.DateTime)
    list_of = partial(fields.DelimitedTuple, cls_or_instance=string(), delimiter="+")


class OptField:
    integer = partial(Field.integer, load_default=None)
    string = partial(Field.string, load_default=None)
    decimal = partial(Field.decimal, load_default=None)
    boolean = partial(Field.boolean, load_default=False)
    positive = partial(Field.positive, load_default=None)
    negative = partial(Field.negative, load_default=None)
    not_positive = partial(Field.not_positive, load_default=None)
    not_negative = partial(Field.not_negative, load_default=None)
    isodate = partial(Field.isodate, load_default=None)
    list_of = partial(Field.list_of, load_default=())


class ReqField:
    integer = partial(Field.integer, required=True)
    string = partial(Field.string, required=True)
    decimal = partial(Field.decimal, required=True)
    boolean = partial(Field.boolean, required=True)
    positive = partial(Field.positive, required=True)
    negative = partial(Field.negative, required=True)
    not_positive = partial(Field.not_positive, required=True)
    not_negative = partial(Field.not_negative, required=True)
    isodate = partial(Field.isodate, required=True)
    list_of = partial(Field.list_of, required=True)


@parser.error_handler
def handle_error(error, *_, **__):
    flask.abort(httpcode.BAD_REQUEST, response=error.messages)


query_paginate = partial(
    query,
    dict(
        page=OptField.positive(),
        page_size=OptField.positive(),
        related=OptField.boolean(load_default=False),
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
