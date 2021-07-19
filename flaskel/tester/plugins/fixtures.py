import pytest

from flaskel.utils import uuid


@pytest.fixture(scope="session")
def session_id():
    return uuid.get_uuid()
