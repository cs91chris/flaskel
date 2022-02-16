import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin

from flaskel import cap, ExtProxy
from .exceptions import MediaError


class MediaMixin(StandardMixin):
    link = sa.Column(sa.String(255), nullable=False, unique=True)
    path = sa.Column(sa.String(255), nullable=False, unique=True)
    filename = sa.Column(sa.String(255))

    def to_dict(self, *_, **__):
        return ObjectDict(id=self.id, link=self.link)


class MediaRepo:
    session = ExtProxy("sqlalchemy.sa.session")
    entity_model = None
    media_model = None

    @classmethod
    def entity_name(cls):
        return cls.entity_model.__tablename__

    @classmethod
    def get(cls, eid):
        return cls.session.query(cls.entity_model).get_or_404(eid)

    @classmethod
    def update(cls, emodel, **kwargs):
        res = cls.media_model(**kwargs)  # pylint: disable=not-callable
        emodel.images.append(res)
        return res

    @classmethod
    def store(cls, emodel):
        try:
            cls.session.add(emodel)
            cls.session.commit()
        except SQLAlchemyError as exc:  # pragma: no cover
            cap.logger.exception(exc)
            cls.session.rollback()
            raise MediaError(exc) from exc

    @classmethod
    def delete(cls, entity_id, media_id):
        try:
            entity = getattr(cls.media_model, cls.entity_name())

            res = (
                cls.session.query(cls.media_model)
                .filter(entity.any(id=entity_id))
                .filter_by(id=media_id)
                .first_or_404()
            )
            cls.session.delete(res)
            cls.session.commit()
            return res
        except SQLAlchemyError as exc:  # pragma: no cover
            cap.logger.exception(exc)
            cls.session.rollback()
            raise MediaError(exc) from exc
