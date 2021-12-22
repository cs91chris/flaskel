# based on https://github.com/enricobarzetti/sqlalchemy_get_or_create
import typing as t

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound as NoResultError
from sqlalchemy.sql import text as text_sql


class SQLASupport:
    def __init__(self, model, session):
        """

        :param model: a model class
        :param session: a session object
        """
        self.session = session
        self.model = model

    @staticmethod
    def _prepare_params(defaults: t.Optional[dict] = None, **kwargs) -> dict:
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

    def _create_object(
        self, lookup: dict, params: dict, lock: bool = False
    ) -> t.Tuple[t.Any, bool]:
        """

        :param lookup: attributes used to find record
        :param params: attributes used to create record
        :param lock: flag used for atomic update
        :return:
        """
        obj = self.model(**params)
        self.session.add(obj)

        with self.session.begin_nested():
            try:
                self.session.flush()
            except IntegrityError:
                self.session.rollback()
                query = self.session.query(self.model).filter_by(**lookup)
                if lock:
                    query = query.with_for_update()
                    obj = query.one()
                return obj, False
            else:
                return obj, True

    def get_or_create(
        self, defaults: t.Optional[dict] = None, **kwargs
    ) -> t.Tuple[t.Any, bool]:
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

    def update_or_create(
        self, defaults: t.Optional[dict] = None, **kwargs
    ) -> t.Tuple[t.Any, bool]:
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

            self.session.merge(obj)
            self.session.flush()

        return obj, False

    @staticmethod
    def exec_from_file(
        url: str,
        filename: str,
        echo: bool = False,
        separator: str = ";\n",
        skip_line_prefixes: tuple = ("--",),
    ):
        """

        :param url:
        :param filename:
        :param echo:
        :param separator:
        :param skip_line_prefixes:
        """
        engine = create_engine(url, echo=echo)
        with engine.connect() as conn, open(filename) as f:
            for statement in f.read().split(separator):
                for skip_line in skip_line_prefixes:
                    if statement.startswith(skip_line):
                        break
                else:
                    conn.execute(text_sql(statement))
