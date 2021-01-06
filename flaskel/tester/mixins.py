import io
import json
import re
from functools import partial

import jsonschema as js
import requests


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
        assert func(actual, expected), \
            error or cls.assert_fail_message.format(
                that=that, actual=actual, expected=expected
            )


class AssertMixin(BaseAssert):
    @classmethod
    def assert_true(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: bool(a) is True,
            error=error, that=f"'{actual}' is True", actual=actual
        )

    @classmethod
    def assert_false(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: bool(a) is False,
            error=error, that=f"'{actual}' is False", actual=actual
        )

    @classmethod
    def assert_none(cls, actual, error=None):
        cls.assert_that(
            lambda a, _: a is None,
            error=error, that=f"'{actual}' is None", actual=actual
        )

    @classmethod
    def assert_equals(cls, actual, expected, error=None):
        def _equals(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a == e

        cls.assert_that(
            lambda a, e: _equals(a, e),
            error=error, that=f"'{actual}' is equals to '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_different(cls, actual, expected, error=None):
        def _different(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a != e

        cls.assert_that(
            lambda a, e: _different(a, e),
            error=error, that=f"'{actual}' is different to '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_in(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: a in e,
            error=error, that=f"'{actual}' is in '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_not_in(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: a not in e,
            error=error, that=f"'{actual}' is not in '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_range(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: e[0] <= a <= e[1],
            error=error, that=f"'{actual}' is in ranger '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_greater(cls, actual, expected, error=None):
        def _greater(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a > e

        cls.assert_that(
            lambda a, e: _greater(a, e),
            error=error, that=f"'{actual}' is greater than '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_less(cls, actual, expected, error=None):
        def _less(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a < e

        cls.assert_that(
            lambda a, e: _less(a, e),
            error=error, that=f"'{actual}' is less than '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_allin(cls, actual, expected, error=None):
        def _allin(a, e):
            return all(i in a for i in e)

        cls.assert_that(
            lambda a, e: _allin(a, e),
            error=error, that=f"'{actual}' are all in '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_type(cls, actual, expected, error=None):
        cls.assert_that(
            lambda a, e: type(a) is e,
            error=error, that=f"type of '{actual}' is '{expected}'",
            actual=actual, expected=expected
        )


class JSONValidatorMixin(BaseAssert):
    jsonschema = js
    dumper = partial(json.dumps, indent=4)
    marker = "3fb539deef7c4e2991f265c0a982f5ea"
    message_format = "{message}\nError in line {line}:\n{report}\n{message}"

    @classmethod
    def error_report(cls, e, json_object, lines_before=8, lines_after=8):
        """
        From: https://github.com/ccpgames/jsonschema-errorprinter/blob/master/jsonschemaerror.py

        Generate a detailed report of a schema validation error.
        'e' is a jsonschema.ValidationError exception that errored on
        'json_object'.
        Steps to discover the location of the validation error:
        1. Traverse the json object using the 'path' in the validation exception
           and replace the offending value with a special marker.
        2. Pretty-print the json object indendented json text.
        3. Search for the special marker in the json text to find the actual
           line number of the error.
        4. Make a report by showing the error line with a context of
          'lines_before' and 'lines_after' number of lines on each side.
        """
        if not e.path:
            return e.message or str(e)

        # Find the object that is erroring, and replace it with the marker.
        for entry in list(e.path)[:-1]:
            json_object = json_object[entry]

        orig, json_object[e.path[-1]] = json_object[e.path[-1]], cls.marker

        # Pretty print the object and search for the marker.
        json_error = cls.dumper(json_object)
        errline = None

        for lineno, text in enumerate(io.StringIO(json_error)):
            if cls.marker in text:
                errline = lineno
                break

        if not errline:
            return e.message or str(e)

        report = []
        json_object[e.path[-1]] = orig
        json_error = cls.dumper(json_object)

        for lineno, text in enumerate(io.StringIO(json_error)):
            line_text = "{:4}: {}".format(lineno + 1, '>' * 3 if lineno == errline else ' ' * 3)
            report.append(line_text + text.rstrip("\n"))

        report = report[max(0, errline - lines_before):errline + 1 + lines_after]
        return cls.message_format.format(
            line=errline + 1,
            report="\n".join(report),
            message=e.message or str(e)
        )

    @classmethod
    def load_from_url(cls, url):
        """

        :param url:
        :return:
        """
        res = requests.get(url)
        res.raise_for_status()
        return res.json()

    @classmethod
    def assert_schema(cls, data, schema):
        """

        :param data:
        :param schema:
        :return:
        """
        valid = True
        message = "json is valid"

        try:
            if schema:
                if type(schema) is str:
                    schema = cls.load_from_url(schema)
                checker = cls.jsonschema.FormatChecker()
                cls.jsonschema.validate(data, schema, format_checker=checker)
        except (cls.jsonschema.ValidationError, cls.jsonschema.SchemaError) as exc:
            valid = False
            message = cls.error_report(exc, data)

        cls.assert_that(
            lambda a, e: a is True,
            actual=valid, error=f"Test that json is valid failed, got: {message}"
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
            lambda a, e: cls.regex_match(a, e),
            error=error, that=f"'{actual}' matches '{expected}'",
            actual=actual, expected=expected
        )

    @classmethod
    def assert_occurrence(cls, actual, expected, occurrence,
                          error=None, greater=False, less=False):
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
            elif less:
                return tmp < occurrence
            else:
                return tmp == occurrence

        operator = "equals to"
        if greater:
            operator = "greater than"
        elif less:
            operator = "less than"

        that = f"occurrences of '{expected}' in '{actual}' are {operator} '{occurrence}'"
        cls.assert_that(
            lambda a, e: find_all(a, e),
            error=error, that=that, actual=actual, expected=expected
        )


class HttpAsserter(AssertMixin, RegexMixin):
    @classmethod
    def assert_status_code(cls, response, code=200,
                           in_range=False, is_in=False, greater=False, less=False):
        """

        :param response:
        :param code:
        :param in_range:
        :param is_in:
        :param greater:
        :param less
        """
        status_code = response.status_code
        if type(code) in (list, tuple):
            if in_range is True:
                cls.assert_range(status_code, code)
            elif is_in is True:
                cls.assert_in(status_code, code)
            else:
                mess = "one of (is_in, in_range) must be true if a list of code is given"
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


class Asserter(
    AssertMixin,
    RegexMixin,
    JSONValidatorMixin,
):
    """single interface that inherits all Asserter mixins"""
