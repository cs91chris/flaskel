SCHEMAS = dict(
    PostRevokeToken={
        "additionalProperties": False,
        "type":                 "object",
        "properties":           {
            "access_token":  {
                "type": "string"
            },
            "refresh_token": {
                "type": "string"
            },
            "device_token":  {
                "type": "string"
            }
        }
    },
    PostAccessToken={
        "additionalProperties": False,
        "type":                 "object",
        "required":             [
            "email",
            "password"
        ],
        "properties":           {
            "email":    {
                "type": "string"
            },
            "password": {
                "type": "string"
            }
        }
    },
    AccessToken={
        "additionalProperties": False,
        "type":                 "object",
        "required":             [
            "access_token",
            "refresh_token",
            "expires_in",
            "issued_at"
        ],
        "properties":           {
            "access_token":  {
                "type": "string"
            },
            "refresh_token": {
                "type": "string"
            },
            "expires_in":    {
                "type": "integer"
            },
            "issued_at":     {
                "type": "integer"
            },
            "token_type":    {
                "type": "string"
            },
            "scope":         {
                "type": "string"
            }
        }
    },
    RefreshToken={
        "additionalProperties": False,
        "type":                 "object",
        "required":             [
            "access_token",
            "expires_in",
            "issued_at"
        ],
        "properties":           {
            "access_token": {
                "type": "string"
            },
            "expires_in":   {
                "type": "integer"
            },
            "issued_at":    {
                "type": "integer"
            },
            "token_type":   {
                "type": "string"
            },
            "scope":        {
                "type": "string"
            }
        }
    },
    ApiProblem={
        "additionalProperties": False,
        "type":                 "object",
        "properties":           {
            "type":     {
                "type": "string"
            },
            "title":    {
                "type": "string"
            },
            "detail":   {
                "type": "string"
            },
            "instance": {
                "type": "string"
            },
            "status":   {
                "type": "integer"
            },
            "response": {
                "type": [
                    "object",
                    "array",
                    "string",
                    "null"
                ]
            }
        }
    }
)
