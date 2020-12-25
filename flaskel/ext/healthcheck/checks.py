def health_sqlalchemy(db):
    """

    :param db:
    :return:
    """
    try:
        with db.engine.connect() as connection:
            connection.execute('SELECT 1')
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover


def health_mongo(db):
    """

    :param db:
    :return:
    """
    try:
        db.db.command('ping')
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover


def health_redis(db):
    """

    :param db:
    :return:
    """
    try:
        db.ping()
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover
