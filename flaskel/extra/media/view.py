import flask
from flask import send_from_directory

from flaskel import HttpMethod
from flaskel.http import httpcode
from flaskel.http.client import cap
from flaskel.views import BaseView
from .exceptions import BadMediaError
from .service import MediaService


class ApiMedia(BaseView):
    service = MediaService
    methods = [
        HttpMethod.POST,
        HttpMethod.DELETE,
    ]

    def dispatch_request(
        self, eid, *_, res_id=None, **__
    ):  # pylint: disable=arguments-differ
        if flask.request.method == HttpMethod.DELETE:
            self.service.delete(eid, res_id)
            return httpcode.NO_CONTENT

        try:
            files = flask.request.files.values()
            return self.service.upload(files, eid)
        except BadMediaError as exc:  # pragma: no cover
            cap.logger.exception(exc)
            return flask.abort(httpcode.BAD_REQUEST, str(exc))


class GetMedia(BaseView):
    default_view_name = "serve_media"
    default_urls = ("/static/media/<path:filename>",)

    def dispatch_request(self, filename, *_, **__):
        return send_from_directory(cap.config.MEDIA.UPLOAD_FOLDER, filename)
