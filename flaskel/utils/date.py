from datetime import datetime

from flaskel.config import DATE_ISO_FORMAT


def from_iso_format(str_date, fmt, exc=True):
    """

    :param str_date: input date with ISO format
    :param fmt: format input date
    :param exc: raise or not exception (default True)
    :return: return formatted date
    """
    if not (exc and str_date):
        return None

    try:
        date = datetime.strptime(str_date, DATE_ISO_FORMAT)
        return date.strftime(fmt)
    except (ValueError, TypeError):
        if exc is True:
            raise


def to_iso_format(str_date, fmt, exc=True):
    """

    :param str_date: input date
    :param fmt: format input date
    :param exc: raise or not exception (default True)
    :return: return date with ISO format
    """
    if not (exc and str_date):
        return None

    try:
        return datetime.strptime(
            str_date, fmt
        ).strftime(DATE_ISO_FORMAT)
    except (ValueError, TypeError):
        if exc is True:
            raise
