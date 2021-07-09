from flaskel.utils.schemas import Fields

SCHEMAS = dict(
    PostRevokeToken=Fields.object(
        properties={
            "access_token":  Fields.string,
            "refresh_token": Fields.string,
            "device_token":  Fields.string
        }
    ),
    PostAccessToken=Fields.object(
        required=["email", "password"],
        properties={
            "email":    Fields.string,
            "password": Fields.string
        }
    ),
    AccessToken=Fields.object(
        required=[
            "access_token",
            "refresh_token",
            "expires_in",
            "issued_at"
        ],
        properties={
            "access_token":  Fields.string,
            "refresh_token": Fields.string,
            "expires_in":    Fields.integer,
            "issued_at":     Fields.integer,
            "token_type":    Fields.string,
            "scope":         Fields.string
        }
    ),
    RefreshToken=Fields.object(
        required=[
            "access_token",
            "expires_in",
            "issued_at"
        ],
        properties={
            "access_token": Fields.string,
            "expires_in":   Fields.integer,
            "issued_at":    Fields.integer,
            "token_type":   Fields.string,
            "scope":        Fields.string
        }
    ),
    ApiProblem=Fields.object(
        properties={
            "type":     Fields.string,
            "title":    Fields.string,
            "detail":   Fields.string,
            "instance": Fields.string,
            "status":   Fields.integer,
            "response": {
                "type": ["object", "array", "string", "null"]
            }
        }
    ),
)

if __name__ == '__main__':  # pragma: no cover
    import json

    print(json.dumps(SCHEMAS))
