from flask import send_from_directory

from flaskel import cap, Response, httpcode
from flaskel.config import config
from flaskel.views import BaseView


class StaticFileView(BaseView):
    default_static_path = "static"
    default_view_name = "static"
    default_urls = ("/static/<path:filename>",)

    def dispatch_request(self, filename, *_, **__):  # pylint: disable=arguments-differ
        return send_from_directory(self.default_static_path, filename)


class SPAView(BaseView):
    template = "index.html"
    default_view_name = "spa"
    default_template_folder = config("SPA_TEMPLATE_FOLDER", default="templates")
    default_static_folder = config("SPA_STATIC_FOLDER", default="webapp")
    default_static_url_path = config("SPA_STATIC_URL_PATH", default="webapp")

    default_urls = (
        "/",
        "/<path:path>",
    )

    def dispatch_request(self, *_, path=None, **__):  # pylint: disable=arguments-differ
        if path is not None:
            return Response.no_content(httpcode.NOT_MODIFIED)
        return cap.send_static_file(self.template)
