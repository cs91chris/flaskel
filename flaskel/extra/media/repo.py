import typing as t

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin
from vbcore.jsonschema.support import Fields

from flaskel import cap, db_session

from .exceptions import MediaError

SCHEMA_MEDIA = Fields.array_object(
    properties={
        "id": Fields.integer,
        "link": Fields.string,
    }
)


class MediaMixin(StandardMixin):
    link = sa.Column(sa.String(255), nullable=False, unique=True)
    path = sa.Column(sa.String(255), nullable=False, unique=True)
    filename = sa.Column(sa.String(255))

    def to_dict(self, *_, **__):
        return ObjectDict(id=self.id, link=self.link)


class MediaRepo:
    entity_model = None
    media_model = None
    session = db_session

    @classmethod
    def entity_name(cls) -> t.Optional[str]:
        if cls.entity_model:
            return cls.entity_model.__tablename__
        return None

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
        except SQLAlchemyError as exc:
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
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            cls.session.rollback()
            raise MediaError(exc) from exc
