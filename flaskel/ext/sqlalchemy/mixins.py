from flask_sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr

from flaskel.ext.sqlalchemy import db
from flaskel.utils.datastruct import ObjectDict


class StandardMixin:
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())


class CatalogMixin:
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """

    @declared_attr
    def __table_args__(self):
        return db.UniqueConstraint('label', 'type_id'),

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    type_id = db.Column(db.Integer)
    description = db.Column(db.String(250))

    def __str__(self):
        return self.label

    def to_dict(self, **kwargs):
        return ObjectDict(
            id=self.id,
            label=self.label,
            description=self.description,
            typeId=self.type_id,
            **kwargs
        )


class CatalogXMixin(CatalogMixin):
    @declared_attr
    def __table_args__(self):
        return db.UniqueConstraint('code', 'type_id'),

    code = db.Column(db.String(20))
    order_id = db.Column(db.Integer, index=True)

    order_by = order_id.asc()

    def __str__(self):
        return f"<{self.code} - {self.label}>"

    def to_dict(self, **kwargs):
        return super().to_dict(
            code=self.code,
            orderId=self.order_id,
            **kwargs
        )


class LoaderMixin:
    values = ()

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """

    @classmethod
    def load_values(cls, *args, **kwargs):
        for d in cls.values:
            db.session.add(cls(**d))
        db.session.commit()

    @classmethod
    def register_loader(cls):
        # noinspection PyUnresolvedReferences
        event.listen(cls.__table__, 'after_create', cls.load_values)
