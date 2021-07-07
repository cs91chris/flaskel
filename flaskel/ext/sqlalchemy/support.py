# based on https://github.com/enricobarzetti/sqlalchemy_get_or_create
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound as NoResultError
from sqlalchemy.sql import text as execute_sql


class SQLASupport:
    def __init__(self, model, session):
        """

        :param model: a model class
        :param session: a session object
        """
        self.session = session
        self.model = model

    @staticmethod
    def _prepare_params(defaults=None, **kwargs):
        """

        :param defaults: overrides kwargs
        :param kwargs: overridden by defaults
        :return: merge of kwargs and defaults
        """
        ret = {}
        defaults = defaults or {}
        ret.update(kwargs)
        ret.update(defaults)
        return ret

    def _create_object(self, lookup, params, lock=False):
        """

        :param lookup: attributes used to find record
        :param params: attributes used to create record
        :param lock: flag used for atomic update
        :return:
        """
        obj = self.model(**params)
        self.session.add(obj)

        try:
            with self.session.begin_nested():
                self.session.flush()
        except IntegrityError:
            self.session.rollback()
            query = self.session.query(self.model).filter_by(**lookup)
            if lock:
                query = query.with_for_update()
            try:
                obj = query.one()
            except NoResultError:
                raise
            else:
                return obj, False
        else:
            return obj, True

    def get_or_create(self, defaults=None, **kwargs):
        """

        :param defaults: attribute used to create record
        :param kwargs: filters used to fetch record or create
        :return:
        """
        try:
            return self.session.query(self.model).filter_by(**kwargs).one(), False
        except NoResultError:
            params = self._prepare_params(defaults, **kwargs)
            return self._create_object(kwargs, params)

    def update_or_create(self, defaults=None, **kwargs):
        """

        :param defaults: attribute used to create record
        :param kwargs: filters used to fetch record or create
        :return:
        """
        defaults = defaults or {}
        with self.session.begin_nested():
            try:
                query = self.session.query(self.model).with_for_update()
                obj = query.filter_by(**kwargs).one()
            except NoResultError:
                params = self._prepare_params(defaults, **kwargs)
                obj, created = self._create_object(kwargs, params, lock=True)
                if created:
                    return obj, created

            for k, v in defaults.items():
                setattr(obj, k, v)

            self.session.add(obj)
            self.session.flush()

        return obj, False

    @staticmethod
    def exec_from_file(db_uri, filename, echo=False):
        """

        :param db_uri:
        :param filename:
        :param echo:
        """
        engine = create_engine(db_uri, echo=echo)
        with engine.connect() as conn, open(filename) as f:
            for statement in f.read().split(';'):
                conn.execute(execute_sql(statement))
