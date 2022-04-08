import typing as t

import jsonschema
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.jsonschema.support import JSONSchema

from flaskel import cap, request
from flaskel.http.exceptions import abort

from .datastruct import ConfigProxy


class PayloadValidator:
    schemas: ObjectDict = ConfigProxy("SCHEMAS")
    validator: t.Type[JSONSchema] = JSONSchema

    @classmethod
    def validate(cls, schema: t.Union[str, dict], strict: bool = True) -> ObjectDict:
        if strict and schema is None:
            abort(httpcode.INTERNAL_SERVER_ERROR, "empty schema")

        payload = request.json
        try:
            schema = cls.schemas.get(schema) if isinstance(schema, str) else schema
            cls.validator.validate(payload, schema, raise_exc=True)
            return payload
        except jsonschema.SchemaError as exc:
            cap.logger.exception(exc)
            return abort(httpcode.INTERNAL_SERVER_ERROR)
        except jsonschema.ValidationError as exc:
            cap.logger.error(cls.validator.error_report(exc, payload))
            reason = dict(cause=exc.cause, message=exc.message, path=exc.path)
            return abort(httpcode.UNPROCESSABLE_ENTITY, response=dict(reason=reason))
