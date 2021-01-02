from flask_sqlalchemy import event

from . import db


class StandardMixin:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())


class CatalogMixin:
    __table_args__ = (db.UniqueConstraint('label', 'type_id'),)

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True)
    type_id = db.Column(db.Integer)
    description = db.Column(db.String(250))

    def __str__(self):
        return self.label

    def to_dict(self):
        return dict(
            id=self.id,
            label=self.label,
            description=self.description,
            typeId=self.type_id
        )


class LoaderMixin:
    instance = db
    values = ()

    # noinspection PyUnusedLocal
    @classmethod
    def load_values(cls, *args, **kwargs):
        for d in cls.values:
            # noinspection PyArgumentList
            cls.instance.session.add(cls(**d))
        cls.instance.session.commit()

    @classmethod
    def register_loader(cls):
        # noinspection PyUnresolvedReferences
        event.listen(cls.__table__, 'after_create', cls.load_values)
