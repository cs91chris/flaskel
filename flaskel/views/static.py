from vbcore.http import httpcode

from flaskel import cap, Response
from flaskel.config import config

from .base import BaseView


class StaticFileView(BaseView):
    default_view_name = "static"
    default_static_path = "static"
    default_urls = ("/static/<path:filename>",)

    def dispatch_request(self, filename, *_, **__):
        return Response.send_file(
            filename=filename,
            max_age=cap.get_send_file_max_age,
            directory=self.default_static_path,
        )


# TODO: check me
class SPAView(BaseView):
    template = "index.html"
    default_view_name = "webapp"
    default_urls = ("/", "/<path:path>")
    default_static_folder = config("SPA_STATIC_FOLDER", default="webapp")
    default_static_url_path = config("SPA_STATIC_URL_PATH", default="/webapp")
    default_template_folder = config("SPA_TEMPLATE_FOLDER", default="templates")

    def dispatch_request(self, *_, path=None, **__):
        if path is not None:
            return Response.no_content(httpcode.NOT_MODIFIED)

        return Response.send_file(
            filename=self.template,
            max_age=cap.get_send_file_max_age,
            directory=self.default_template_folder,
        )
