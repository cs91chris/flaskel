from datetime import datetime
from operator import itemgetter

from dateutil import parser
from flask import current_app as cap


def or_na(item):
    """

    :param item:
    :return:
    """
    if not item:
        return cap.config["NOT_AVAILABLE_DESC"]
    return item


def yes_or_no(item):
    """

    :param item:
    :return:
    """
    return "yes" if bool(item) else "no"


def reverse(s):
    """

    :param s:
    :return:
    """
    return s[::-1]


def pretty_date(date, fmt=None):
    """

    :param date:
    :param fmt:
    :return:
    """
    fmt = fmt or cap.config["PRETTY_DATE"]
    if date:
        if isinstance(date, datetime):
            return date.strftime(fmt)

        return parser.parse(date).strftime(fmt)
    return ""


def order_by(data, item, descending=False, silent=True):
    """

    :param data: list of objects
    :param item: item of the object according to which to order
    :param descending: descending order
    :param silent: raise or not exception
    :return:
    """
    try:
        return sorted(data, key=itemgetter(item), reverse=descending)
    except KeyError:
        if silent:
            return data
        raise


def truncate(data, n, term=None):
    """

    :param data: input string
    :param n: max length of string
    :param term: string to append to output
    :return:
    """
    if term is None:
        term = "..."

    return "{}{}".format(data[:n], term)


def human_file_size(size, max_index=None):
    """

    :param size:
    :param max_index:
    :return:
    """
    idx = 0
    size = int(size or 0)
    scale = cap.config["HUMAN_FILE_SIZE_SCALE"]
    divider = cap.config["HUMAN_FILE_SIZE_DIVIDER"]
    max_index = max_index or len(scale)

    if size < divider:
        return f"{size} B"

    for idx in range(0, max_index):
        size /= divider
        if size < divider:
            break

    return "{:.2f} {}".format(size, scale[idx])
