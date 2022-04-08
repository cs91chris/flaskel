from vbcore.http import httpcode, HttpMethod

from flaskel import abort, cap, request
from flaskel.views import BaseView
from flaskel.views.static import StaticFileView

from .exceptions import BadMediaError
from .service import MediaService


class ApiMedia(BaseView):
    service = MediaService
    methods = [
        HttpMethod.POST,
        HttpMethod.DELETE,
    ]
    default_urls = (
        "/resources/<int:eid>/media",
        "/resources/<int:eid>/media/<int:res_id>",
    )

    def dispatch_request(self, eid, *_, res_id=None, **__):
        if request.method == HttpMethod.DELETE:
            self.service.delete(eid, res_id)
            return httpcode.NO_CONTENT

        try:
            files = request.files.values()
            return self.service.upload(files, eid)
        except BadMediaError as exc:
            cap.logger.exception(exc)
            return abort(httpcode.BAD_REQUEST, str(exc))


class GetMedia(StaticFileView):
    default_static_path = "static"
    default_view_name = "serve_media"
    default_urls = ("/static/media/<path:filename>",)
