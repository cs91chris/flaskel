import typing as t

import flask
from vbcore.http import HttpMethod

from flaskel.flaskel import Response

from .base import BaseView


class RenderTemplate(BaseView):
    methods: t.List[str] = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    template: str = "index.html"

    def __init__(
        self,
        template: t.Optional[str] = None,
        content_type: t.Optional[str] = None,
        **kwargs,
    ):
        self._params = kwargs
        self._content_type = content_type
        self._template = template or self.template

    def service(self, *_, **kwargs):
        return kwargs or self._params

    def response(self, data, **kwargs):
        return Response(data, mimetype=self._content_type, **kwargs)

    def dispatch_request(self, *_, **__):
        params = self.service()
        template = flask.render_template(self._template, **params)
        return self.response(template)


class RenderTemplateString(RenderTemplate):
    def dispatch_request(self, *_, **__):
        params = self.service()
        template = flask.render_template_string(self._template, **params)
        return self.response(template)
