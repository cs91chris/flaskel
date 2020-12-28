from datetime import datetime

from flaskel import cap


def from_iso_format(str_date, fmt, exc=True):
    """

    :param str_date: input date with ISO format
    :param fmt: format input date
    :param exc: raise or not exception (default True)
    :return: return formatted date
    """
    if not (exc or str_date):
        return None   # pragma: no cover

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
        return None   # pragma: no cover

    try:
        date_time = datetime.strptime(str_date, fmt)
        return date_time.strftime(cap.config.DATE_ISO_FORMAT)
    except (ValueError, TypeError):
        if exc is True:
            raise  # pragma: no cover
