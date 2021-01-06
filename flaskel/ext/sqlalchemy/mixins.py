from flask_sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from flaskel.utils.datastruct import ObjectDict
from . import db


class StandardMixin:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())


class CatalogMixin:
    @declared_attr
    def __table_args__(self):
        return db.UniqueConstraint('label', 'type_id'),

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    type_id = db.Column(db.Integer)
    description = db.Column(db.String(250))

    def __str__(self):
        return self.label

    def to_dict(self):
        return ObjectDict(
            id=self.id,
            label=self.label,
            description=self.description,
            typeId=self.type_id
        )


class LoaderMixin:
    values = ()

    # noinspection PyUnusedLocal
    @classmethod
    def load_values(cls, *args, **kwargs):
        for d in cls.values:
            # noinspection PyArgumentList
            db.session.add(cls(**d))
        db.session.commit()

    @classmethod
    def register_loader(cls):
        # noinspection PyUnresolvedReferences
        event.listen(cls.__table__, 'after_create', cls.load_values)
