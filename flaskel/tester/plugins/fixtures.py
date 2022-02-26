# pylint: disable=redefined-outer-name
import pytest

from flaskel.utils.datastruct import ExtProxy


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
