# pylint: disable=redefined-outer-name

from typing import Optional, Union, Tuple, Dict

import pytest

from flaskel import ExtProxy
from flaskel.tester.helpers import url_for
from flaskel.utils import uuid


@pytest.fixture(scope="session")
def session_id():
    return uuid.get_uuid()


@pytest.fixture()
def db_session():
    return ExtProxy("sqlalchemy.db.session")


@pytest.fixture()
def db_save(db_session):
    def _save(items: list):
        for i in items:
            db_session.merge(i)
        db_session.commit()

    return _save


@pytest.fixture()
def auth_token(test_client):
    def get_access_token(
        token: Optional[str] = None,
        token_type: str = "Bearer",
        is_query: bool = False,
        credentials: Optional[Union[Dict[str, str], Tuple[str, str]]] = None,
        access_view: str = "auth.token_access",
    ):
        if token is not None:
            return dict(Authorization=f"Bearer {token}")

        if not credentials:
            config = test_client.application.config
            credentials = dict(email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD)
        if isinstance(credentials, tuple):
            credentials = dict(email=credentials[0], password=credentials[1])

        tokens = test_client.post(url_for(access_view), json=credentials)
        if is_query is True:
            return dict(jwt={tokens.json.access_token})

        return dict(Authorization=f"{token_type} {tokens.json.access_token}")

    return get_access_token


@pytest.fixture(scope="session")
def apikey(auth_token):
    return auth_token()
