import flask

from flaskel import cap, httpcode
from .base import BaseView


class ApiDocTemplate(BaseView):
    apispec_view = 'apispec'

    def dispatch_request(self):
        if not cap.config.APIDOCS_ENABLED:
            flask.abort(httpcode.NOT_FOUND)

        rapidoc_version = cap.config.RAPIDOC_VERSION or '8.4.3'
        rapidoc_theme = cap.config.RAPIDOC_THEME or 'dark'
        page_title = f"{cap.config.APP_NAME} - API DOCS"

        spec_url = flask.url_for(
            self.apispec_view,
            _external=True,
            _scheme=cap.config.PREFERRED_URL_SCHEME
        )

        return f"""
            <!doctype html>
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
            </html>
        """


class ApiSpecTemplate(BaseView):
    api_version = '1.0.0'
    url_version = '/v1'

    def dispatch_request(self):
        if not cap.config.APIDOCS_ENABLED:
            flask.abort(httpcode.NOT_FOUND)

        data = cap.config.APISPEC
        scheme = cap.config.PREFERRED_URL_SCHEME or 'http'
        current_server = f"{scheme}://{cap.config.SERVER_NAME}/{self.url_version}"

        try:
            data['info']['version'] = self.api_version
            variables = data['servers'][0]['variables']
            variables['version']['default'] = self.url_version
            variables['host']['default'] = current_server
        except (AttributeError, IndexError, KeyError, TypeError) as exc:
            cap.logger.debug(str(exc))

        return data
