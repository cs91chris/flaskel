import typing as t

from flask_sqlalchemy import Model
from vbcore.datastruct import ObjectDict


class SQLAModel(Model):
    __table__ = None

    def columns(self) -> t.List[str]:
        if self.__table__ is not None:
            return list(self.__table__.columns.keys())
        return []

    @classmethod
    def get_one(
        cls, *args, raise_not_found: bool = True, to_dict: bool = True, **kwargs
    ):
        res = cls.query.filter(*args).filter_by(**kwargs)

        if raise_not_found:
            res = res.first_or_404()
        else:
            res = res.first()
            if res is None:
                return None

        if to_dict is True:
            return res.to_dict()
        return res

    @classmethod
    def prepare_collection_filters(cls, params: dict) -> list:
        # stub method
        _ = params
        return []

    @classmethod
    def query_collection(cls, *_, params: t.Optional[dict] = None, **kwargs):
        filters = cls.prepare_collection_filters(params or {})
        return cls.query.filter(*filters).filter_by(**kwargs)

    @classmethod
    def get_list(
        cls,
        *args,
        to_dict: bool = True,
        restricted: bool = False,
        order_by: t.Optional[t.Tuple] = None,
        page: t.Optional[int] = None,
        page_size: t.Optional[int] = None,
        max_per_page: t.Optional[int] = None,
        **kwargs,
    ):
        q = cls.query_collection(*args, **kwargs)

        if order_by is not None:
            q = q.order_by(*order_by)

        if page or page_size:
            q = q.paginate(page, page_size, False, max_per_page)
            res = q.items
            if to_dict is False:
                return q
        else:
            res = q.all()

        if to_dict is True:
            return (r.to_dict(restricted) for r in res)
        return res

    def update(self, attributes: dict):
        for attr, val in attributes.items():
            if attr in self.columns():
                setattr(self, attr, val)

        return self

    def to_dict(self, restricted: bool = False) -> dict:
        _ = restricted
        # noinspection PyUnresolvedReferences
        cols = self.columns()  # type: ignore
        return ObjectDict(**{c: getattr(self, c, None) for c in cols})
