import typing as t

import flask
import jsonschema
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.jsonschema.support import JSONSchema

from flaskel.http.client import cap
from flaskel.utils.datastruct import ExtProxy


class PayloadValidator:
    schemas: ObjectDict = ExtProxy("SCHEMAS")
    validator: t.Type[JSONSchema] = JSONSchema

    @classmethod
    def validate(cls, schema: t.Union[str, dict], strict: bool = True) -> ObjectDict:
        if strict and schema is None:
            flask.abort(httpcode.INTERNAL_SERVER_ERROR, "empty schema")

        payload = flask.request.json
        try:
            schema = cls.schemas.get(schema) if isinstance(schema, str) else schema
            cls.validator.validate(payload, schema, raise_exc=True)
            return payload
        except jsonschema.SchemaError as exc:
            cap.logger.exception(exc)
            return flask.abort(httpcode.INTERNAL_SERVER_ERROR)
        except jsonschema.ValidationError as exc:
            cap.logger.error(cls.validator.error_report(exc, payload))
            reason = dict(cause=exc.cause, message=exc.message, path=exc.path)
            return flask.abort(
                httpcode.UNPROCESSABLE_ENTITY, response=dict(reason=reason)
            )
