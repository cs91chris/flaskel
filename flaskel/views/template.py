from flask.views import View
from flask import render_template


# noinspection PyMethodMayBeStatic
class RenderTemplate(View):
    methods = ['GET', 'POST']

    def __init__(self, template):
        """

        :param template:
        """
        self._template = template

    def service(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        return kwargs

    def dispatch_request(self):
        """

        :return:
        """
        params = self.service()
        return render_template(self._template, **params)

    @classmethod
    def register(cls, app, name, url, **kwargs):
        """

        :param app:
        :param name:
        :param url:
        :param kwargs:
        """
        view_func = cls.as_view(name, **kwargs)
        app.add_url_rule(url, view_func=view_func)
