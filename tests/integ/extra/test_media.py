import io

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, relationship  # type: ignore[attr-defined]
from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin, UserMixin
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.tester.asserter import Asserter

from flaskel.ext.default import builder, Database
from flaskel.extra.media.repo import (
    MediaMixin,
    MediaRepo as BaseMediaRepo,
    SCHEMA_MEDIA,
)
from flaskel.extra.media.service import MediaService as BaseMediaService
from flaskel.extra.media.view import ApiMedia, GetMedia
from flaskel.tester.helpers import ApiTester, url_for

db = Database()


class User(db.Model, UserMixin):  # type: ignore[name-defined]
    __tablename__ = "users"

    images: Mapped["Media"] = relationship(
        "Media",
        secondary="media_users",
        back_populates="users",
        lazy="joined",
        cascade="all",
    )


class MediaUser(db.Model, StandardMixin):  # type: ignore[name-defined]
    __tablename__ = "media_users"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    media_id = sa.Column(sa.Integer, sa.ForeignKey("media.id"))


class Media(db.Model, MediaMixin):  # type: ignore[name-defined]
    __tablename__ = "media"

    users: Mapped["User"] = relationship(
        "User", secondary="media_users", back_populates="images"
    )

    def to_dict(self, *_, **__):
        return MediaMixin.to_dict(self)


class MediaRepo(BaseMediaRepo):
    media_model = Media
    entity_model = User


class MediaService(BaseMediaService):
    media_repo = MediaRepo


class ApiMediaUser(ApiMedia):
    service = MediaService
    default_view_name = "media_users"
    default_urls = (
        "/users/<int:eid>/media",
        "/users/<int:eid>/media/<int:res_id>",
    )
    decorators = [
        builder.on_format("json"),
    ]


def test_media(testapp, session_save, tmpdir):
    user_id = 1
    user = User(id=user_id, email="test@mail.com", password="password")
    files = [
        (io.BytesIO(b"image content 1"), "test_file1.png"),
        (io.BytesIO(b"image content 2"), "test_file2.png"),
        (io.BytesIO(b"image content 3"), "test_file3.png"),
    ]

    tmpdir.mkdir("static")
    tmpdir.mkdir("static/media")
    tmpdir.mkdir("static/media/users")
    GetMedia.default_static_path = tmpdir.join("static", "media").strpath

    app = testapp(
        extensions={"database": (db,)},
        config=ObjectDict(
            MEDIA=ObjectDict(
                ALLOWED_EXTENSIONS="jpg,png",
                EXTERNAL_URL="localhost:5000/static/media",
                UPLOAD_FOLDER=GetMedia.default_static_path,
            ),
        ),
        views=(
            GetMedia,
            ApiMediaUser,
        ),
    )
    client = ApiTester(app.test_client())

    with app.app_context():
        session_save([user])

    response = client.post(
        mimetype=ContentTypeEnum.JSON,
        schema=SCHEMA_MEDIA,
        url=url_for("media_users", eid=user_id),
        headers={HeaderEnum.CONTENT_TYPE: ContentTypeEnum.FORM_DATA},
        data={"file1": files[0], "file2": files[1]},
    )
    Asserter.assert_equals(len(response.json), 2)

    for media in response.json:
        client.get(
            url=url_for("serve_media", filename=media.link),
            mimetype=ContentTypeEnum.PNG,
        )

        client.delete(
            url=url_for("media_users", eid=user_id, res_id=media.id),
            status=httpcode.NO_CONTENT,
        )
