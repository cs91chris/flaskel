from datetime import datetime
from operator import itemgetter

from dateutil import parser
from flask import current_app as cap


def or_na(item):
    if not item:
        return cap.config["NOT_AVAILABLE_DESC"]
    return item


def yes_or_no(item):
    return "yes" if bool(item) else "no"


def reverse(s):
    return s[::-1]


def pretty_date(date, fmt=None):
    fmt = fmt or cap.config["PRETTY_DATE"]
    if date:
        if isinstance(date, datetime):
            return date.strftime(fmt)

        return parser.parse(date).strftime(fmt)
    return ""


def order_by(data, item, descending=False, silent=True):
    try:
        return sorted(data, key=itemgetter(item), reverse=descending)
    except KeyError:
        if silent:
            return data
        raise


def truncate(data, n, term=None):
    if term is None:
        term = "..."

    return f"{data[:n]}{term}"


def human_file_size(size, max_index=None):
    idx = 0
    size = int(size or 0)
    scale = cap.config["HUMAN_FILE_SIZE_SCALE"]
    divider = cap.config["HUMAN_FILE_SIZE_DIVIDER"]
    max_index = max_index or len(scale)

    if size < divider:
        return f"{size} B"

    for _idx in range(0, max_index):
        idx = _idx
        size /= divider
        if size < divider:
            break

    return "{:.2f} {}".format(size, scale[idx])
