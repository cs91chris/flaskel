import io
from functools import partial

import flask
import jsonschema
from flask import current_app as cap

from flaskel.http.client import HTTPClient, httpcode
from flaskel.utils.datastruct import ConfigProxy, ObjectDict

SCHEMAS = ConfigProxy('SCHEMAS')


class JSONSchema:
    loader = partial(flask.json.loads)
    dumper = partial(flask.json.dumps, indent=4)
    marker = "3fb539deef7c4e2991f265c0a982f5ea"
    message_format = "{message}\nError in line {line}:\n{report}\n{message}"

    @classmethod
    def load_from_url(cls, url):
        """

        :param url:
        :return:
        """
        res = HTTPClient(url, raise_on_exc=True).get(url)
        return res.body

    @classmethod
    def load_from_file(cls, file):
        """

        :param file:
        :return:
        """
        if file.startswith('file://'):
            file = file[7:]

        with open(file) as f:
            return cls.loader(f.read())

    @classmethod
    def validate(cls, data, schema, raise_exc=False, pretty_error=True, checker=None):
        """

        :param data:
        :param schema:
        :param raise_exc:
        :param pretty_error:
        :param checker:
        :return:
        """
        if not schema:
            return True

        if type(schema) is str:
            if schema.startswith('https://') or schema.startswith('http://'):
                schema = cls.load_from_url(schema)
            if schema.startswith('file://'):
                schema = cls.load_from_file(schema)

        try:
            checker = checker or jsonschema.FormatChecker()
            jsonschema.validate(data, schema, format_checker=checker)
        except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            if not raise_exc:
                if pretty_error:
                    cap.logger.error(cls.error_report(exc, data))
                else:
                    cap.logger.exception(exc)
                return False
            raise
        return True

    @classmethod
    def error_report(cls, e, json_object, lines_before=8, lines_after=8):
        """
        From: https://github.com/ccpgames/jsonschema-errorprinter/blob/master/jsonschemaerror.py

        Generate a detailed report of a schema validation error.
        'e' is a jsonschema.ValidationError exception raised on 'json_object'.

        Steps to discover the location of the validation error:
            1. Traverse the json object using the 'path' in the validation exception
               and replace the offending value with a special marker.
            2. Pretty-print the json object indented json text.
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
        err_line = None

        for lineno, text in enumerate(io.StringIO(json_error)):
            if cls.marker in text:
                err_line = lineno
                break

        if not err_line:
            return e.message or str(e)

        report = []
        json_object[e.path[-1]] = orig
        json_error = cls.dumper(json_object)

        for lineno, text in enumerate(io.StringIO(json_error)):
            line_text = "{:4}: {}".format(lineno + 1, '>' * 3 if lineno == err_line else ' ' * 3)
            report.append(line_text + text.rstrip("\n"))

        report = report[max(0, err_line - lines_before):err_line + 1 + lines_after]
        return cls.message_format.format(
            line=err_line + 1,
            report="\n".join(report),
            message=e.message or str(e)
        )


class PayloadValidator:
    schemas = SCHEMAS
    validator = JSONSchema

    @classmethod
    def validate(cls, schema, strict=True):
        """

        :param schema:
        :param strict:
        :return:
        """
        if strict and not schema:
            flask.abort(httpcode.INTERNAL_SERVER_ERROR, 'empty schema')

        payload = flask.request.json
        try:
            schema = cls.schemas.get(schema) if type(schema) is str else schema
            cls.validator.validate(payload, schema, raise_exc=True)
            return payload
        except jsonschema.SchemaError as exc:
            cap.logger.exception(exc)
            flask.abort(httpcode.INTERNAL_SERVER_ERROR)
        except jsonschema.ValidationError as exc:
            cap.logger.error(cls.validator.error_report(exc, payload))
            reason = dict(cause=exc.cause, message=exc.message, path=exc.path)
            flask.abort(httpcode.UNPROCESSABLE_ENTITY, response=dict(reason=reason))


class Fields:
    null = ObjectDict(type="null")
    integer = ObjectDict(type="integer")
    string = ObjectDict(type="string")
    number = ObjectDict(type="number")
    boolean = ObjectDict(type="boolean")
    datetime = ObjectDict(type="string", format="date-time")

    class Opt:
        integer = ObjectDict(type=["integer", "null"])
        string = ObjectDict(type=["string", "null"])
        number = ObjectDict(type=["number", "null"])
        boolean = ObjectDict(type=["boolean", "null"])

    @classmethod
    def oneof(cls, *args, **kwargs):
        return ObjectDict(
            oneOf=args if len(args) > 1 else (*args, cls.null),
            **kwargs
        )

    @classmethod
    def anyof(cls, *args, **kwargs):
        return ObjectDict(
            anyOf=args if len(args) > 1 else (*args, cls.null),
            **kwargs
        )

    @classmethod
    def object(
            cls, required=(), properties=None,
            all_required=False, additional=False, **kwargs
    ):
        properties = properties or {}
        if not required and all_required is True:
            required = list(properties.keys())

        return ObjectDict(
            type="object",
            additionalProperties=additional,
            required=required,
            properties=properties,
            **kwargs
        )

    @classmethod
    def array(cls, items, min_items=0, **kwargs):
        return ObjectDict(
            type="array",
            minItems=min_items,
            items=items,
            **kwargs
        )

    @classmethod
    def array_object(cls, min_items=0, **kwargs):
        return ObjectDict(
            type="array",
            minItems=min_items,
            items=cls.object(**kwargs)
        )
