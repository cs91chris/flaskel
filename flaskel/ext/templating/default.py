from . import filters, functions

DEFAULT_FILTERS = {
    "or_na": filters.or_na,
    "yes_or_no": filters.yes_or_no,
    "reverse": filters.reverse,
    "pretty_date": filters.pretty_date,
    "order_by": filters.order_by,
    "truncate": filters.truncate,
    "human_byte_size": filters.human_byte_size,
}

DEFAULT_FUNCTIONS = {
    "now": (functions.now, None),
}
