import flask
from flask.views import View


class BaseView(View):
    methods = ['GET']

    def dispatch_request(self):
        """
        Must be implemented in every subclass
        """
        raise NotImplementedError

    @classmethod
    def register(cls, app, name=None, url=None, **kwargs):
        """

        :param app: Flask app or blueprint
        :param name: optional view name
        :param url: optional url or view name
        :param kwargs: argument passed to cls constructor
        """
        name = name or cls.__name__
        view_func = cls.as_view(name, **kwargs)
        app.add_url_rule(url or f"/{name}", view_func=view_func)


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
