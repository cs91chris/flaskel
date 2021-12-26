REGEX_OBJECT_KEY = "^[a-zA-Z0-9\\.\\-_]+$"


class Definitions:
    reference = "#/definitions/Reference"
    schema = "#/definitions/Schema"
    server = "#/definitions/Server"
    external_documentation = "#/definitions/ExternalDocumentation"
    response = "#/definitions/Response"
    header = "#/definitions/Header"
    parameter = "#/definitions/Parameter"
    example = "#/definitions/Example"
    mediatype = "#/definitions/MediaType"
    example_xor_examples = "#/definitions/ExampleXORExamples"


# pylint: disable=C0302
SCHEMA = {
    "id": "https://spec.openapis.org/oas/3.0/schema/2019-04-02",
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "Validation schema for OpenAPI Specification 3.0.X.",
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string", "pattern": "^3\\.0\\.\\d(-.+)?$"},
        "info": {"$ref": "#/definitions/Info"},
        "externalDocs": {"$ref": Definitions.external_documentation},
        "servers": {"type": "array", "items": {"$ref": Definitions.server}},
        "security": {
            "type": "array",
            "items": {"$ref": "#/definitions/SecurityRequirement"},
        },
        "tags": {
            "type": "array",
            "items": {"$ref": "#/definitions/Tag"},
            "uniqueItems": True,
        },
        "paths": {"$ref": "#/definitions/Paths"},
        "components": {"$ref": "#/definitions/Components"},
    },
    "patternProperties": {"^x-": {}},
    "additionalProperties": False,
    "definitions": {
        "Reference": {
            "type": "object",
            "required": ["$ref"],
            "patternProperties": {
                "^\\$ref$": {"type": "string", "format": "uri-reference"}
            },
        },
        "Info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "termsOfService": {"type": "string", "format": "uri-reference"},
                "contact": {"$ref": "#/definitions/Contact"},
                "license": {"$ref": "#/definitions/License"},
                "version": {"type": "string"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Contact": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "url": {"type": "string", "format": "uri-reference"},
                "email": {"type": "string", "format": "email"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "License": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "url": {"type": "string", "format": "uri-reference"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Server": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {"type": "string"},
                "description": {"type": "string"},
                "variables": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/definitions/ServerVariable"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "ServerVariable": {
            "type": "object",
            "required": ["default"],
            "properties": {
                "enum": {"type": "array", "items": {"type": "string"}},
                "default": {"type": "string"},
                "description": {"type": "string"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Components": {
            "type": "object",
            "properties": {
                "schemas": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.schema},
                                {"$ref": Definitions.reference},
                            ]
                        }
                    },
                },
                "responses": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": Definitions.response},
                            ]
                        }
                    },
                },
                "parameters": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": Definitions.parameter},
                            ]
                        }
                    },
                },
                "examples": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": Definitions.example},
                            ]
                        }
                    },
                },
                "requestBodies": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": "#/definitions/RequestBody"},
                            ]
                        }
                    },
                },
                "headers": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": Definitions.header},
                            ]
                        }
                    },
                },
                "securitySchemes": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": "#/definitions/SecurityScheme"},
                            ]
                        }
                    },
                },
                "links": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": "#/definitions/Link"},
                            ]
                        }
                    },
                },
                "callbacks": {
                    "type": "object",
                    "patternProperties": {
                        REGEX_OBJECT_KEY: {
                            "oneOf": [
                                {"$ref": Definitions.reference},
                                {"$ref": "#/definitions/Callback"},
                            ]
                        }
                    },
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "multipleOf": {
                    "type": "number",
                    "minimum": 0,
                    "exclusiveMinimum": True,
                },
                "maximum": {"type": "number"},
                "exclusiveMaximum": {"type": "boolean", "default": False},
                "minimum": {"type": "number"},
                "exclusiveMinimum": {"type": "boolean", "default": False},
                "maxLength": {"type": "integer", "minimum": 0},
                "minLength": {"type": "integer", "minimum": 0, "default": 0},
                "pattern": {"type": "string", "format": "regex"},
                "maxItems": {"type": "integer", "minimum": 0},
                "minItems": {"type": "integer", "minimum": 0, "default": 0},
                "uniqueItems": {"type": "boolean", "default": False},
                "maxProperties": {"type": "integer", "minimum": 0},
                "minProperties": {"type": "integer", "minimum": 0, "default": 0},
                "required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "enum": {
                    "type": "array",
                    "items": {},
                    "minItems": 1,
                    "uniqueItems": False,
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "array",
                        "boolean",
                        "integer",
                        "number",
                        "object",
                        "string",
                    ],
                },
                "not": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                    ]
                },
                "allOf": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": Definitions.schema},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "oneOf": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": Definitions.schema},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "anyOf": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": Definitions.schema},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "items": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                    ]
                },
                "properties": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": Definitions.schema},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "additionalProperties": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                        {"type": "boolean"},
                    ],
                    "default": True,
                },
                "description": {"type": "string"},
                "format": {"type": "string"},
                "default": {},
                "nullable": {"type": "boolean", "default": False},
                "discriminator": {"$ref": "#/definitions/Discriminator"},
                "readOnly": {"type": "boolean", "default": False},
                "writeOnly": {"type": "boolean", "default": False},
                "example": {},
                "externalDocs": {"$ref": Definitions.external_documentation},
                "deprecated": {"type": "boolean", "default": False},
                "xml": {"$ref": "#/definitions/XML"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Discriminator": {
            "type": "object",
            "required": ["propertyName"],
            "properties": {
                "propertyName": {"type": "string"},
                "mapping": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "XML": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "namespace": {"type": "string", "format": "uri"},
                "prefix": {"type": "string"},
                "attribute": {"type": "boolean", "default": False},
                "wrapped": {"type": "boolean", "default": False},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Response": {
            "type": "object",
            "required": ["description"],
            "properties": {
                "description": {"type": "string"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": Definitions.header},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "content": {
                    "type": "object",
                    "additionalProperties": {"$ref": Definitions.mediatype},
                },
                "links": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": "#/definitions/Link"},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "MediaType": {
            "type": "object",
            "properties": {
                "schema": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                    ]
                },
                "example": {},
                "examples": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": Definitions.example},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "encoding": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/definitions/Encoding"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
            "allOf": [{"$ref": Definitions.example_xor_examples}],
        },
        "Example": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "value": {},
                "externalValue": {"type": "string", "format": "uri-reference"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Header": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "required": {"type": "boolean", "default": False},
                "deprecated": {"type": "boolean", "default": False},
                "allowEmptyValue": {"type": "boolean", "default": False},
                "style": {"type": "string", "enum": ["simple"], "default": "simple"},
                "explode": {"type": "boolean"},
                "allowReserved": {"type": "boolean", "default": False},
                "schema": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                    ]
                },
                "content": {
                    "type": "object",
                    "additionalProperties": {"$ref": Definitions.mediatype},
                    "minProperties": 1,
                    "maxProperties": 1,
                },
                "example": {},
                "examples": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": Definitions.example},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
            "allOf": [
                {"$ref": Definitions.example_xor_examples},
                {"$ref": "#/definitions/SchemaXORContent"},
            ],
        },
        "Paths": {
            "type": "object",
            "patternProperties": {
                "^\\/": {"$ref": "#/definitions/PathItem"},
                "^x-": {},
            },
            "additionalProperties": False,
        },
        "PathItem": {
            "type": "object",
            "properties": {
                "$ref": {"type": "string"},
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "servers": {"type": "array", "items": {"$ref": Definitions.server}},
                "parameters": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": Definitions.parameter},
                            {"$ref": Definitions.reference},
                        ]
                    },
                    "uniqueItems": True,
                },
            },
            "patternProperties": {
                "^(get|put|post|delete|options|head|patch|trace)$": {
                    "$ref": "#/definitions/Operation"
                },
                "^x-": {},
            },
            "additionalProperties": False,
        },
        "Operation": {
            "type": "object",
            "required": ["responses"],
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "externalDocs": {"$ref": Definitions.external_documentation},
                "operationId": {"type": "string"},
                "parameters": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": Definitions.parameter},
                            {"$ref": Definitions.reference},
                        ]
                    },
                    "uniqueItems": True,
                },
                "requestBody": {
                    "oneOf": [
                        {"$ref": "#/definitions/RequestBody"},
                        {"$ref": Definitions.reference},
                    ]
                },
                "responses": {"$ref": "#/definitions/Responses"},
                "callbacks": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": "#/definitions/Callback"},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
                "deprecated": {"type": "boolean", "default": False},
                "security": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/SecurityRequirement"},
                },
                "servers": {"type": "array", "items": {"$ref": Definitions.server}},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Responses": {
            "type": "object",
            "properties": {
                "default": {
                    "oneOf": [
                        {"$ref": Definitions.response},
                        {"$ref": Definitions.reference},
                    ]
                }
            },
            "patternProperties": {
                "^[1-5](?:\\d{2}|XX)$": {
                    "oneOf": [
                        {"$ref": Definitions.response},
                        {"$ref": Definitions.reference},
                    ]
                },
                "^x-": {},
            },
            "minProperties": 1,
            "additionalProperties": False,
        },
        "SecurityRequirement": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
        "Tag": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "externalDocs": {"$ref": Definitions.external_documentation},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "ExternalDocumentation": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "description": {"type": "string"},
                "url": {"type": "string", "format": "uri-reference"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "ExampleXORExamples": {
            "description": "Example and examples are mutually exclusive",
            "not": {"required": ["example", "examples"]},
        },
        "SchemaXORContent": {
            "description": "Schema and content are mutually exclusive, at least one is required",
            "not": {"required": ["schema", "content"]},
            "oneOf": [
                {"required": ["schema"]},
                {
                    "required": ["content"],
                    "description": "Some properties are not allowed if content is present",
                    "allOf": [
                        {"not": {"required": ["style"]}},
                        {"not": {"required": ["explode"]}},
                        {"not": {"required": ["allowReserved"]}},
                        {"not": {"required": ["example"]}},
                        {"not": {"required": ["examples"]}},
                    ],
                },
            ],
        },
        "Parameter": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "in": {"type": "string"},
                "description": {"type": "string"},
                "required": {"type": "boolean", "default": False},
                "deprecated": {"type": "boolean", "default": False},
                "allowEmptyValue": {"type": "boolean", "default": False},
                "style": {"type": "string"},
                "explode": {"type": "boolean"},
                "allowReserved": {"type": "boolean", "default": False},
                "schema": {
                    "oneOf": [
                        {"$ref": Definitions.schema},
                        {"$ref": Definitions.reference},
                    ]
                },
                "content": {
                    "type": "object",
                    "additionalProperties": {"$ref": Definitions.mediatype},
                    "minProperties": 1,
                    "maxProperties": 1,
                },
                "example": {},
                "examples": {
                    "type": "object",
                    "additionalProperties": {
                        "oneOf": [
                            {"$ref": Definitions.example},
                            {"$ref": Definitions.reference},
                        ]
                    },
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
            "required": ["name", "in"],
            "allOf": [
                {"$ref": Definitions.example_xor_examples},
                {"$ref": "#/definitions/SchemaXORContent"},
                {"$ref": "#/definitions/ParameterLocation"},
            ],
        },
        "ParameterLocation": {
            "description": "Parameter location",
            "oneOf": [
                {
                    "description": "Parameter in path",
                    "required": ["required"],
                    "properties": {
                        "in": {"enum": ["path"]},
                        "style": {
                            "enum": ["matrix", "label", "simple"],
                            "default": "simple",
                        },
                        "required": {"enum": [True]},
                    },
                },
                {
                    "description": "Parameter in query",
                    "properties": {
                        "in": {"enum": ["query"]},
                        "style": {
                            "enum": [
                                "form",
                                "spaceDelimited",
                                "pipeDelimited",
                                "deepObject",
                            ],
                            "default": "form",
                        },
                    },
                },
                {
                    "description": "Parameter in header",
                    "properties": {
                        "in": {"enum": ["header"]},
                        "style": {"enum": ["simple"], "default": "simple"},
                    },
                },
                {
                    "description": "Parameter in cookie",
                    "properties": {
                        "in": {"enum": ["cookie"]},
                        "style": {"enum": ["form"], "default": "form"},
                    },
                },
            ],
        },
        "RequestBody": {
            "type": "object",
            "required": ["content"],
            "properties": {
                "description": {"type": "string"},
                "content": {
                    "type": "object",
                    "additionalProperties": {"$ref": Definitions.mediatype},
                },
                "required": {"type": "boolean", "default": False},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "SecurityScheme": {
            "oneOf": [
                {"$ref": "#/definitions/APIKeySecurityScheme"},
                {"$ref": "#/definitions/HTTPSecurityScheme"},
                {"$ref": "#/definitions/OAuth2SecurityScheme"},
                {"$ref": "#/definitions/OpenIdConnectSecurityScheme"},
            ]
        },
        "APIKeySecurityScheme": {
            "type": "object",
            "required": ["type", "name", "in"],
            "properties": {
                "type": {"type": "string", "enum": ["apiKey"]},
                "name": {"type": "string"},
                "in": {"type": "string", "enum": ["header", "query", "cookie"]},
                "description": {"type": "string"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "HTTPSecurityScheme": {
            "type": "object",
            "required": ["scheme", "type"],
            "properties": {
                "scheme": {"type": "string"},
                "bearerFormat": {"type": "string"},
                "description": {"type": "string"},
                "type": {"type": "string", "enum": ["http"]},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
            "oneOf": [
                {
                    "description": "Bearer",
                    "properties": {"scheme": {"enum": ["bearer"]}},
                },
                {
                    "description": "Non Bearer",
                    "not": {"required": ["bearerFormat"]},
                    "properties": {"scheme": {"not": {"enum": ["bearer"]}}},
                },
            ],
        },
        "OAuth2SecurityScheme": {
            "type": "object",
            "required": ["type", "flows"],
            "properties": {
                "type": {"type": "string", "enum": ["oauth2"]},
                "flows": {"$ref": "#/definitions/OAuthFlows"},
                "description": {"type": "string"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "OpenIdConnectSecurityScheme": {
            "type": "object",
            "required": ["type", "openIdConnectUrl"],
            "properties": {
                "type": {"type": "string", "enum": ["openIdConnect"]},
                "openIdConnectUrl": {"type": "string", "format": "uri-reference"},
                "description": {"type": "string"},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "OAuthFlows": {
            "type": "object",
            "properties": {
                "implicit": {"$ref": "#/definitions/ImplicitOAuthFlow"},
                "password": {"$ref": "#/definitions/PasswordOAuthFlow"},
                "clientCredentials": {"$ref": "#/definitions/ClientCredentialsFlow"},
                "authorizationCode": {
                    "$ref": "#/definitions/AuthorizationCodeOAuthFlow"
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "ImplicitOAuthFlow": {
            "type": "object",
            "required": ["authorizationUrl", "scopes"],
            "properties": {
                "authorizationUrl": {"type": "string", "format": "uri-reference"},
                "refreshUrl": {"type": "string", "format": "uri-reference"},
                "scopes": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "PasswordOAuthFlow": {
            "type": "object",
            "required": ["tokenUrl"],
            "properties": {
                "tokenUrl": {"type": "string", "format": "uri-reference"},
                "refreshUrl": {"type": "string", "format": "uri-reference"},
                "scopes": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "ClientCredentialsFlow": {
            "type": "object",
            "required": ["tokenUrl"],
            "properties": {
                "tokenUrl": {"type": "string", "format": "uri-reference"},
                "refreshUrl": {"type": "string", "format": "uri-reference"},
                "scopes": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "AuthorizationCodeOAuthFlow": {
            "type": "object",
            "required": ["authorizationUrl", "tokenUrl"],
            "properties": {
                "authorizationUrl": {"type": "string", "format": "uri-reference"},
                "tokenUrl": {"type": "string", "format": "uri-reference"},
                "refreshUrl": {"type": "string", "format": "uri-reference"},
                "scopes": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
        },
        "Link": {
            "type": "object",
            "properties": {
                "operationId": {"type": "string"},
                "operationRef": {"type": "string", "format": "uri-reference"},
                "parameters": {"type": "object", "additionalProperties": {}},
                "requestBody": {},
                "description": {"type": "string"},
                "server": {"$ref": Definitions.server},
            },
            "patternProperties": {"^x-": {}},
            "additionalProperties": False,
            "not": {
                "description": "Operation Id and Operation Ref are mutually exclusive",
                "required": ["operationId", "operationRef"],
            },
        },
        "Callback": {
            "type": "object",
            "additionalProperties": {"$ref": "#/definitions/PathItem"},
            "patternProperties": {"^x-": {}},
        },
        "Encoding": {
            "type": "object",
            "properties": {
                "contentType": {"type": "string"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"$ref": Definitions.header},
                },
                "style": {
                    "type": "string",
                    "enum": ["form", "spaceDelimited", "pipeDelimited", "deepObject"],
                },
                "explode": {"type": "boolean"},
                "allowReserved": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
}


if __name__ == "__main__":
    import json

    print(json.dumps(SCHEMA))
