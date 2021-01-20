import flask

from .base import BaseView


class RenderTemplate(BaseView):
    methods = ['GET', 'POST']

    def __init__(self, template, content_type=None, **kwargs):
        """

        :param template:
        """
        self._params = kwargs
        self._template = template
        self._content_type = content_type

    # noinspection PyUnusedLocal
    def service(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        return kwargs or self._params

    def response(self, data, **kwargs):
        return flask.Response(data, mimetype=self._content_type, **kwargs)

    def dispatch_request(self):
        return self.response(
            flask.render_template(self._template, **self.service())
        )


class RenderTemplateString(RenderTemplate):
    def dispatch_request(self):
        return self.response(
            flask.render_template_string(self._template, **self.service())
        )
