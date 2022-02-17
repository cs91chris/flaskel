from flask import url_for
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode

from flaskel.flaskel import cap, request
from flaskel.http.exceptions import abort
from flaskel.views.base import BaseView
from flaskel.views.template import RenderTemplateString


class ApiDocTemplate(RenderTemplateString):
    apispec_view = "api.apispec"
    default_view_name = "apidocs"
    default_urls = ("/apidocs",)

    template = """<!doctype html>
<html>
    <head>
        <meta charset="utf-8"/>
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
        <meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no"/>
        <title>{{page_title}}</title>
        <script type="module"
            src="https://unpkg.com/rapidoc@{{rapidoc_version}}/dist/rapidoc-min.js">
        </script>
    </head>
    <body>
        <rapi-doc
            theme="{{rapidoc_theme}}" spec-url="{{spec_url}}"
            render-style="view" font-size="large"
        ></rapi-doc>
    </body>
</html>"""

    def service(self, *_, **__) -> dict:
        if not cap.config.APIDOCS_ENABLED:
            return abort(httpcode.NOT_FOUND)

        proto = cap.config.PREFERRED_URL_SCHEME
        return dict(
            rapidoc_version=cap.config.RAPIDOC_VERSION or "9",
            rapidoc_theme=cap.config.RAPIDOC_THEME or "dark",
            page_title=f"{cap.config.APP_NAME} - API DOCS",
            spec_url=url_for(self.apispec_view, _external=True, _scheme=proto),
        )


class ApiSpecTemplate(BaseView):
    default_view_name = "apispec"
    default_urls = ("/apidoc.json",)

    def __init__(self, version: str = "1.0.0", context_path: str = ""):
        self._api_version = version
        self._context_path = f"{request.environ['SCRIPT_NAME']}/{context_path}"

    def dispatch_request(self, *_, **__):
        if not cap.config.APIDOCS_ENABLED:
            abort(httpcode.NOT_FOUND)

        return self.set_variables(cap.config.APISPEC)

    def set_variables(self, apispec: ObjectDict) -> ObjectDict:
        try:
            apispec.info.version = self._api_version
            variables = apispec.servers[0].variables
            variables["context"]["default"] = self._context_path
            scheme = cap.config.PREFERRED_URL_SCHEME or "http"
            variables["host"]["default"] = f"{scheme}://{cap.config.SERVER_NAME}"
        except Exception as exc:  # pylint: disable=broad-except
            cap.logger.exception(exc)

        return apispec
