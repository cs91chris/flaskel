from flaskel.ext.sqlalchemy.mixins import db, StandardMixin


class Dummy(db.Model, StandardMixin):
    __tablename__ = 'items'

    item = db.Column(db.String(200), nullable=False)

    def to_dict(self, *_, **__):
        return dict(id=self.id, item=self.item)
