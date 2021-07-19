from flaskel.utils.schemas import default

SCHEMAS = dict(
    PostRevokeToken=default.SCHEMAS.POST_REVOKE_TOKEN,
    PostAccessToken=default.SCHEMAS.POST_ACCESS_TOKEN,
    AccessToken=default.SCHEMAS.ACCESS_TOKEN,
    RefreshToken=default.SCHEMAS.REFRESH_TOKEN,
    ApiProblem=default.SCHEMAS.API_PROBLEM,
)

if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(SCHEMAS))
