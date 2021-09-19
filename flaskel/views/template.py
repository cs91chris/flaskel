import typing as t

import flask

from flaskel import HttpMethod
from .base import BaseView


class RenderTemplate(BaseView):
    methods: t.List[str] = [
        HttpMethod.GET,
        HttpMethod.POST,
    ]

    template: str = "index.html"

    def __init__(self, template=None, content_type=None, **kwargs):
        """

        :param template:
        :param content_type:
        """
        self._params = kwargs
        self._content_type = content_type
        self._template = template or self.template

    # noinspection PyUnusedLocal
    def service(self, *_, **kwargs):
        """

        :param kwargs:
        :return:
        """
        return kwargs or self._params

    def response(self, data, **kwargs):
        return flask.Response(data, mimetype=self._content_type, **kwargs)

    def dispatch_request(self, *_, **__):
        params = self.service()
        template = flask.render_template(self._template, **params)
        return self.response(template)


class RenderTemplateString(RenderTemplate):
    def dispatch_request(self, *_, **__):
        params = self.service()
        template = flask.render_template_string(self._template, **params)
        return self.response(template)
