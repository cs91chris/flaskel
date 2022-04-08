import os
import typing as t

from vbcore.uuid import get_uuid
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flaskel import cap, ConfigProxy

from .exceptions import MediaError
from .repo import MediaRepo


class MediaService:
    media_repo = MediaRepo
    obfuscate_filename = True
    config = ConfigProxy("MEDIA")

    @classmethod
    def get_ext(cls, filename) -> t.Optional[str]:
        if "." in filename:
            return filename.split(".", 1)[-1].lower()
        return None

    @classmethod
    def generate_filepath(cls, eid, filename: str) -> t.Tuple[str, str]:
        ext = cls.get_ext(filename)
        entity_name = cls.media_repo.entity_name()
        if cls.obfuscate_filename is True:
            filename = get_uuid()
        else:
            filename = secure_filename(filename)

        filename = f"{eid}-{filename}.{ext}"
        filepath = os.path.join(entity_name, filename)
        url = "/".join((entity_name, filename))
        return url, filepath

    @classmethod
    def check_file(cls, file: FileStorage):
        if not file.filename:
            raise MediaError("missing file name")
        if cls.get_ext(file.filename) not in cls.config.ALLOWED_EXTENSIONS:
            raise MediaError("file extension not allowed")

    @classmethod
    def upload(cls, files: t.Iterable[FileStorage], eid) -> list:
        medias = []
        emodel = cls.media_repo.get(eid)
        for f in files:
            cls.check_file(f)
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
        except OSError as exc:
            cap.logger.exception(exc)
