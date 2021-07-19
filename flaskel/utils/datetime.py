try:  # pragma: no cover
    import holidays
except ImportError:  # pragma: no cover
    holidays = None

from datetime import datetime

from dateutil.parser import parse as date_parse

from flaskel.flaskel import cap


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


class DateHelper:
    def __init__(self, *args, **kwargs):
        assert holidays is not None, "you must install holidays"
        self._holidays = holidays.CountryHoliday(*args, **kwargs)

    @property
    def holidays(self):
        return self._holidays  # pragma: no cover

    def all_holidays(self):
        return list(self._holidays.items())

    @staticmethod
    def country_holidays(*args, **kwargs):
        return holidays.CountryHoliday(*args, **kwargs)

    @staticmethod
    def is_weekend(curr_date, **kwargs):
        """

        :param curr_date: date instance or string date
        :param kwargs: passed to dateutil.parser.parse
        :return: boolean, True if is weekend
        """
        if isinstance(curr_date, str):
            curr_date = date_parse(curr_date, **kwargs)

        return curr_date.weekday() > 4

    @staticmethod
    def change_format(str_date, out_fmt, in_fmt=None, raise_exc=True):
        """

        :param str_date: input string date
        :param out_fmt: format output date
        :param in_fmt: format input date (optional: could be detected from string)
        :param raise_exc: raise or not exception (default True)
        :return: return formatted date
        """
        if not (raise_exc or str_date):
            return None  # pragma: no cover

        try:
            if in_fmt:
                date_time = datetime.strptime(str_date, in_fmt)
            else:
                date_time = date_parse(str_date)
            return date_time.strftime(out_fmt)
        except (ValueError, TypeError):
            if raise_exc is True:
                raise  # pragma: no cover
        return None


# for backwards compatibility
def from_iso_format(str_date, fmt, exc=True):
    return DateHelper.change_format(
        str_date, in_fmt=cap.config.DATE_ISO_FORMAT, out_fmt=fmt, raise_exc=exc
    )


# for backwards compatibility
def to_iso_format(str_date, fmt=None, exc=True):
    return DateHelper.change_format(
        str_date, in_fmt=fmt, out_fmt=cap.config.DATE_ISO_FORMAT, raise_exc=exc
    )
