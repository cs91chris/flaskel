import flask

from flaskel.flaskel import cap, httpcode
from flaskel.views.base import BaseView


class ApiDocTemplate(BaseView):
    apispec_view = 'api.apispec'
    default_view_name = 'apidocs'
    default_urls = ['/apidocs']

    def dispatch_request(self):
        if not cap.config.APIDOCS_ENABLED:
            flask.abort(httpcode.NOT_FOUND)  # pragma: no cover

        rapidoc_version = cap.config.RAPIDOC_VERSION or '8.4.3'
        rapidoc_theme = cap.config.RAPIDOC_THEME or 'dark'
        page_title = f"{cap.config.APP_NAME} - API DOCS"

        spec_url = flask.url_for(
            self.apispec_view,
            _external=True,
            _scheme=cap.config.PREFERRED_URL_SCHEME
        )

        return f"""<!doctype html>
<html>
    <head>
        <meta charset="utf-8"/>
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
        <meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no"/>
        <title>{page_title}</title>
        <script type="module"
            src="https://unpkg.com/rapidoc@{rapidoc_version}/dist/rapidoc-min.js">
        </script>
    </head>
    <body>
        <rapi-doc theme="{rapidoc_theme}" spec-url="{spec_url}"></rapi-doc>
    </body>
</html>"""


class ApiSpecTemplate(BaseView):
    default_view_name = 'apispec'
    default_urls = ['/apidoc.json']

    def __init__(self, version='1.0.0', context_path=''):
        """

        :param version:
        :param context_path:
        """
        self._api_version = version
        self._context_path = f"{flask.request.environ['SCRIPT_NAME']}/{context_path}"

    def dispatch_request(self):
        if not cap.config.APIDOCS_ENABLED:
            flask.abort(httpcode.NOT_FOUND)  # pragma: no cover

        return self.set_variables(cap.config.APISPEC)

    def set_variables(self, apispec):
        """

        :param apispec:
        :return:
        """
        try:
            apispec.info.version = self._api_version
            variables = apispec.servers[0].variables
            variables['context']['default'] = self._context_path
            scheme = cap.config.PREFERRED_URL_SCHEME or 'http'
            variables['host']['default'] = f"{scheme}://{cap.config.SERVER_NAME}"
        except (AttributeError, IndexError, KeyError, TypeError) as exc:  # pragma: no cover
            cap.logger.exception(exc)
        return apispec
