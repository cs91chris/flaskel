from flaskel.utils.schemas.default import SCHEMAS as DEFAULT_SCHEMAS

LOCALE = "it_IT.utf8"
ERROR_PAGE = "errors.html"
ERROR_HANDLER = "web"

SCHEMAS = dict(
    PostRevokeToken=DEFAULT_SCHEMAS.POST_REVOKE_TOKEN,
    PostAccessToken=DEFAULT_SCHEMAS.POST_ACCESS_TOKEN,
    AccessToken=DEFAULT_SCHEMAS.ACCESS_TOKEN,
    RefreshToken=DEFAULT_SCHEMAS.REFRESH_TOKEN,
    ApiProblem=DEFAULT_SCHEMAS.API_PROBLEM,
)

if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(SCHEMAS))
