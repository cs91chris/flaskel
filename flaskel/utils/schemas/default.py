from flaskel import ObjectDict
from flaskel.utils.schemas.support import Fields

SCHEMAS = ObjectDict(
    JSONRPC=ObjectDict(
        REQUEST=Fields.oneof(
            Fields.ref("/definitions/request", description="An individual request"),
            Fields.array(
                items=Fields.ref("/definitions/request"),
                description="An array of requests",
            ),
            **Fields.schema,
            description="A JSON RPC 2.0 request",
            definitions={
                "request": Fields.object(
                    required=["jsonrpc", "method"],
                    properties={
                        "jsonrpc": Fields.enum("2.0"),
                        "method": Fields.string,
                        "params": Fields.type("array", "object"),
                        "id": Fields.type(
                            "string",
                            "number",
                            "null",
                            note=[
                                "While allowed, null should be avoided: "
                                "http://www.jsonrpc.org/specification#id1",
                                "While allowed, a number with a fractional part should be avoided: "
                                "http://www.jsonrpc.org/specification#id2",
                            ],
                        ),
                    },
                )
            },
        ),
        RESPONSE=Fields.oneof(
            Fields.ref("/definitions/response"),
            Fields.array(items=Fields.ref("/definitions/response")),
            **Fields.schema,
            definitions={
                "response": Fields.type(
                    "array",
                    "object",
                    required=["jsonrpc"],
                    properties={
                        "jsonrpc": Fields.enum("2.0"),
                        "id": Fields.type("string", "number", "null"),
                        "result": Fields.type("array", "object", "null"),
                        "error": Fields.type(
                            "array",
                            "object",
                            properties={
                                "code": Fields.number,
                                "message": Fields.string,
                            },
                        ),
                    },
                )
            },
        ),
    ),
    POST_REVOKE_TOKEN=Fields.object(
        all_required=False,
        properties={
            "access_token": Fields.string,
            "refresh_token": Fields.string,
            "device_token": Fields.string,
        },
    ),
    POST_ACCESS_TOKEN=Fields.object(
        properties={"email": Fields.string, "password": Fields.string}
    ),
    ACCESS_TOKEN=Fields.object(
        required=["access_token", "refresh_token", "expires_in", "issued_at"],
        properties={
            "access_token": Fields.string,
            "refresh_token": Fields.string,
            "expires_in": Fields.integer,
            "issued_at": Fields.integer,
            "token_type": Fields.string,
            "scope": Fields.Opt.string,
        },
    ),
    REFRESH_TOKEN=Fields.object(
        required=["access_token", "expires_in", "issued_at"],
        properties={
            "access_token": Fields.string,
            "expires_in": Fields.integer,
            "issued_at": Fields.integer,
            "token_type": Fields.string,
            "scope": Fields.Opt.string,
        },
    ),
    API_PROBLEM=Fields.object(
        properties={
            "type": Fields.string,
            "title": Fields.string,
            "detail": Fields.string,
            "instance": Fields.string,
            "status": Fields.integer,
            "response": Fields.type("object", "array", "string", "null"),
        }
    ),
    HEALTH_CHECK=Fields.object(
        **Fields.schema,
        properties={
            "status": Fields.string,
            "checks": Fields.object(
                patternProperties={
                    ".": Fields.object(
                        properties={
                            "status": Fields.string,
                            "output": Fields.type("null", "string", "object"),
                        }
                    )
                }
            ),
            "links": Fields.object(properties={"about": Fields.Opt.string}),
        },
    ),
)

if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(SCHEMAS))
