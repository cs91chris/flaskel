from flaskel import ObjectDict

# noinspection PyUnresolvedReferences
from flaskel.tester import helpers as h  # noqa

VIEWS = ObjectDict(
    access_token="auth.access_token",
    refresh_token="auth.refresh_token",
    revoke_token="auth.revoke_token",
)
