import io
import json
import re
from functools import partial

import jsonschema as js
import requests


class BaseAssert:
    assert_fail_message = "Test that {that} failed: got {actual}, expected {expected}"

    @classmethod
    def assert_that(cls, func, actual, expected, that="", error=None):
        """

        :param func:
        :param actual:
        :param expected:
        :param that:
        :param error:
        """
        assert func(actual, expected), \
            error or cls.assert_fail_message.format(
                that=that,
                actual=actual,
                expected=expected
            )


class AssertMixin(BaseAssert):
    @classmethod
    def assert_true(cls, actual, error=None):
        """

        :param actual:
        :param error:
        """
        cls.assert_that(
            lambda a, e: bool(a) is True,
            error=error,
            that=f"{actual} is True",
            actual=actual,
            expected=True
        )

    @classmethod
    def assert_false(cls, actual, error=None):
        """

        :param actual:
        :param error:
        """
        cls.assert_that(
            lambda a, e: bool(a) is False,
            error=error,
            that=f"{actual} is False",
            actual=actual,
            expected=True
        )

    @classmethod
    def assert_none(cls, actual, error=None):
        """

        :param actual:
        :param error:
        """
        cls.assert_that(
            lambda a, e: bool(a) is False,
            error=error,
            that=f"{actual} is None",
            actual=actual,
            expected=True
        )

    @classmethod
    def assert_equals(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """

        def _equals(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a == e

        cls.assert_that(
            lambda a, e: _equals(a, e),
            error=error,
            that=f"{actual} = {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_in(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """
        cls.assert_that(
            lambda a, e: a in e,
            error=error,
            that=f"{actual} is in {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_range(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """
        cls.assert_that(
            lambda a, e: e[0] <= a <= e[1],
            error=error,
            that=f"{actual} is in {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_greater(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """

        def _greater(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a > e

        cls.assert_that(
            lambda a, e: _greater(a, e),
            error=error,
            that=f"{actual} is greater than {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_less(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """

        def _less(a, e):
            if type(a) in (list, tuple):
                a = len(a)
            return a < e

        cls.assert_that(
            lambda a, e: _less(a, e),
            error=error,
            that=f"{actual} is less than {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_allin(cls, actual, expected, error=None):
        """

        :param actual:
        :param expected:
        :param error:
        """

        def _allin(a, e):
            return all(i in a for i in e)

        cls.assert_that(
            lambda a, e: _allin(a, e),
            error=error,
            that=f"{actual} are all in {expected}",
            actual=actual,
            expected=expected
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
            lambda a, e: a is e,
            actual=valid,
            expected=True,
            error=f"Test that json is valid failed, got: {message}"
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
            error=error,
            that=f"{actual} match {expected}",
            actual=actual,
            expected=expected
        )

    @classmethod
    def assert_occurrence(cls, actual, expected, occurrence, error=None, greater=False, less=False):
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

        that = f"occurrences of {expected} in {actual} are {operator} {occurrence}"

        cls.assert_that(
            lambda a, e: find_all(a, e),
            error=error,
            that=that,
            actual=actual,
            expected=expected
        )


class Asserter(
    AssertMixin,
    JSONValidatorMixin,
    RegexMixin
):
    """single interface that inherits all Asserter mixins"""
