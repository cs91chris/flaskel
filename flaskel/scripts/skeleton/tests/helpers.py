import typing as t

# noinspection PyUnresolvedReferences
from flaskel.tester.helpers import *  # noqa F403 pylint: disable=unused-wildcard-import,wildcard-import


class Views(t.NamedTuple):
    access_token: str
    refresh_token: str
    revoke_token: str


VIEWS = Views(
    access_token="auth.access_token",
    refresh_token="auth.refresh_token",
    revoke_token="auth.revoke_token",
)
