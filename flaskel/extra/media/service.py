import os
import typing as t

from flaskel import ConfigProxy, uuid
from flaskel.http.client import cap
from .exceptions import MediaError
from .repo import MediaRepo


class MediaService:
    media_repo = MediaRepo
    obfuscate_filename = True
    config = ConfigProxy("MEDIA")

    @classmethod
    def get_ext(cls, filename):
        if "." in filename:
            return filename.rsplit(".", 1)[-1].lower()
        return None

    @classmethod
    def generate_filepath(cls, eid, filename) -> t.Tuple[str, str]:
        ext = cls.get_ext(filename)
        entity_name = cls.media_repo.entity_name()
        if cls.obfuscate_filename is True:
            filename = uuid.get_uuid()

        filename = f"{eid}-{filename}.{ext}"
        filepath = os.path.join(entity_name, filename)
        url = "/".join((entity_name, filename))
        return url, filepath

    @classmethod
    def upload(cls, files, eid):
        medias = []
        emodel = cls.media_repo.get(eid)
        for f in files:
            if not f.filename:
                raise MediaError("missing file name")  # pragma: no cover
            if cls.get_ext(f.filename) not in cls.config.ALLOWED_EXTENSIONS:
                raise MediaError("file extension not allowed")  # pragma: no cover

            url, filepath = cls.generate_filepath(emodel.id, f.filename)
            f.save(os.path.join(cls.config.UPLOAD_FOLDER, filepath))
            res = cls.media_repo.update(
                emodel, link=url, path=filepath, filename=f.filename
            )
            medias.append(res)

        cls.media_repo.store(emodel)
        return medias

    @classmethod
    def delete(cls, eid, res_id):
        res = cls.media_repo.delete(eid, res_id)

        try:
            filepath = os.path.join(*cls.config.UPLOAD_FOLDER.split("/"), res.path)
            if os.path.isfile(filepath):
                os.remove(filepath)
        except OSError as exc:  # pragma: no cover
            cap.logger.exception(exc)
