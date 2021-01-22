from datetime import datetime

from flaskel import cap


class Millis:
    seconds = 1000
    minute = seconds * 60
    hour = minute * 60
    day = hour * 24


class Seconds:
    millis = 1000
    minute = 60
    hour = minute * 60
    day = hour * 24


class Minutes:
    seconds = 60
    hour = 60
    day = hour * 24


class Day:
    hours = 24
    minutes = hours * 60
    seconds = minutes * 60


def from_iso_format(str_date, fmt, exc=True):
    """

    :param str_date: input date with ISO format
    :param fmt: format input date
    :param exc: raise or not exception (default True)
    :return: return formatted date
    """
    if not (exc or str_date):
        return None  # pragma: no cover

    try:
        date_time = datetime.strptime(str_date, cap.config.DATE_ISO_FORMAT)
        return date_time.strftime(fmt)
    except (ValueError, TypeError):
        if exc is True:
            raise  # pragma: no cover


def to_iso_format(str_date, fmt, exc=True):
    """

    :param str_date: input date
    :param fmt: format input date
    :param exc: raise or not exception (default True)
    :return: return date with ISO format
    """
    if not (exc or str_date):
        return None  # pragma: no cover

    try:
        date_time = datetime.strptime(str_date, fmt)
        return date_time.strftime(cap.config.DATE_ISO_FORMAT)
    except (ValueError, TypeError):
        if exc is True:
            raise  # pragma: no cover
