import re

import jsonschema

from flaskel.utils.schemas import JSONSchema


class BaseAssert:
    assert_fail_message = "Test that {that} failed: got {actual}, expected {expected}"

    @classmethod
    def assert_that(cls, func, actual, expected=None, that="", error=None):
        """

        :param func:
        :param actual:
        :param expected:
        :param that:
        :param error:
        """
        assert func(actual, expected), error or cls.assert_fail_message.format(
            that=that, actual=actual, expected=expected
        )

    @classmethod
    def assert_true(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: bool(a) is True,
            error=error,
            that=f"'{actual}' is True",
            actual=actual,
        )

    @classmethod
    def assert_false(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: bool(a) is False,
            error=error,
            that=f"'{actual}' is False",
            actual=actual,
        )

    @classmethod
    def assert_none(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: a is None,
            error=error,
            that=f"'{actual}' is None",
            actual=actual,
        )

    @classmethod
    def assert_equals(cls, actual, expected, error=None):
        def _equals(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a == e

        cls.assert_that(
            _equals,
            error=error,
            that=f"'{actual}' is equals to '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_different(cls, actual, expected, error=None):
        def _different(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a != e

        cls.assert_that(
            _different,
            error=error,
            that=f"'{actual}' is different to '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_in(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: a in e,
            error=error,
            that=f"'{actual}' is in '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_not_in(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: a not in e,
            error=error,
            that=f"'{actual}' is not in '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_range(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: e[0] <= a <= e[1],
            error=error,
            that=f"'{actual}' is in ranger '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_greater(cls, actual, expected, error=None):
        def _greater(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a > e

        cls.assert_that(
            _greater,
            error=error,
            that=f"'{actual}' is greater than '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_less(cls, actual, expected, error=None):
        def _less(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a < e

        cls.assert_that(
            _less,
            error=error,
            that=f"'{actual}' is less than '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_allin(cls, actual, expected, error=None):
        def _allin(a, e):
            return all(i in a for i in e)

        cls.assert_that(
            _allin,
            error=error,
            that=f"'{actual}' are all in '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_type(cls, actual, expected, error=None):
        cls.assert_that(
            isinstance,
            error=error,
            that=f"type of '{actual}' is '{expected}'",
            actual=actual,
            expected=expected,
        )


class JSONValidatorMixin(BaseAssert, JSONSchema):
    @classmethod
    def assert_schema(cls, data, schema, strict=True):
        """

        :param data:
        :param schema:
        :param strict:
        :return:
        """
        if strict and not schema:
            cls.assert_that(
                lambda a, e: a is not None, actual=schema, error="Missing schema"
            )
        try:
            cls.validate(data, schema, raise_exc=True)
            valid, message = True, None
        except jsonschema.ValidationError as exc:
            valid, message = False, cls.error_report(exc, data)

        cls.assert_that(
            lambda a, e: a is True,
            actual=valid,
            error=f"Test that json is valid failed, got: {message}",
        )


class RegexMixin(BaseAssert):
    @classmethod
    def regex_find(cls, data, pattern, index=None):
        """

        :param data:
        :param pattern:
        :param index:
        :return:
        """
        occ = re.findall(pattern, data)
        if index is not None:
            if len(occ) > index:
                return occ[index]
            return None
        return occ

    @classmethod
    def regex_match(cls, data, pattern):
        """

        :param data:
        :param pattern:
        :return:
        """
        return bool(re.search(pattern, data))

    @classmethod
    def assert_match(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """
        cls.assert_that(
            cls.regex_match,
            error=error,
            that=f"'{actual}' matches '{expected}'",
            actual=actual,
            expected=expected,
        )

    @classmethod
    def assert_occurrence(
        cls, actual, expected, occurrence, error=None, greater=False, less=False
    ):
        """

        :param actual:
        :param expected:
        :param occurrence:
        :param error:
        :param greater:
        :param less:
        """

        def find_all(a, e):
            tmp = len(cls.regex_find(a, e))
            if greater:
                return tmp > occurrence
            if less:
                return tmp < occurrence
            return tmp == occurrence

        operator = "equals to"
        if greater:
            operator = "greater than"
        elif less:
            operator = "less than"

        that = (
            f"occurrences of '{expected}' in '{actual}' are {operator} '{occurrence}'"
        )
        cls.assert_that(
            find_all, error=error, that=that, actual=actual, expected=expected
        )


class HttpAsserter(RegexMixin):
    @classmethod
    def assert_status_code(
        cls, response, code=200, in_range=False, is_in=False, greater=False, less=False
    ):
        """

        :param response:
        :param code:
        :param in_range:
        :param is_in:
        :param greater:
        :param less
        """
        status_code = response.status_code or response.status
        if type(code) in (list, tuple):
            if in_range is True:
                cls.assert_range(status_code, code)
            elif is_in is True:
                cls.assert_in(status_code, code)
            else:
                mess = (
                    "one of (is_in, in_range) must be true if a list of code is given"
                )
                cls.assert_true(False, error=mess)
        else:
            if greater is True:
                cls.assert_greater(status_code, code)
            elif less is True:
                cls.assert_less(status_code, code)
            else:
                cls.assert_equals(status_code, code)

    @classmethod
    def assert_header(cls, response, name, value=None, is_in=False, regex=None):
        """

        :param response:
        :param name:
        :param value:
        :param is_in:
        :param regex:
        """
        header = response.headers.get(name)
        if is_in is True and value is not None:
            cls.assert_in(value, header)
        elif regex is not None:
            cls.assert_match(value, header)
        else:
            if is_in is True:
                cls.assert_in(name, response.headers)
            else:
                cls.assert_equals(value, header)

    def assert_headers(self, response, headers):
        """

        :param response:
        :param headers: {"name": {"value":"", "is_in": False, "regex": None}}
        :return:
        """
        for k, v in headers.items():
            self.assert_header(response, name=k, **v)

    @classmethod
    def assert_content_type(cls, response, value=None, is_in=True, regex=None):
        cls.assert_header(
            response, name="Content-Type", value=value, is_in=is_in, regex=regex
        )


class Asserter(
    HttpAsserter,
    JSONValidatorMixin,
):
    """single interface that inherits all Asserter mixins"""
