from collections import deque

import pytest
from vbcore.datastruct import ObjectDict
from vbcore.jsonschema.support import Fields
from vbcore.tester.mixins import Asserter

from flaskel import PayloadValidator
from flaskel.http.exceptions import InternalServerError, UnprocessableEntity
from flaskel.utils.schemas.default import SCHEMAS


def test_payload_validator_ok(flaskel_app):
    payload = {"a": 1}
    schema = Fields.object(properties={"a": Fields.integer})
    with flaskel_app.test_request_context(json=payload):
        Asserter.assert_equals(
            PayloadValidator.validate(schema),
            ObjectDict(**payload),
        )


def test_payload_validator_fail(flaskel_app):
    payload = {
        "type": "string",
        "instance": Fields.string,
        "status": "string",
    }

    with pytest.raises(UnprocessableEntity) as error:
        with flaskel_app.test_request_context(json=payload):
            PayloadValidator.validate(SCHEMAS.API_PROBLEM)

    Asserter.assert_equals(
        error.value.response,
        {
            "reason": {
                "cause": None,
                "message": "'title' is a required property",
                "path": deque([]),
            }
        },
    )


def test_payload_validator_error(flaskel_app):
    payload = {"a": "A"}
    schema = ObjectDict(
        type="object",
        additionalProperties="1",
    )

    with pytest.raises(InternalServerError) as error:
        with flaskel_app.test_request_context(json=payload):
            PayloadValidator.validate(schema)

    Asserter.assert_none(error.value.response)
