from flaskel.utils.datetime import DateHelper


class FlaskDateHelper:
    def __init__(self, app=None, **kwargs):
        """

        :param app:
        :param kwargs:
        """
        self._helper = None
        self.iso_format = None

        if app is not None:
            self.init_app(app, **kwargs)  # pragma: no cover

    def init_app(self, app, helper=None, helper_class=DateHelper, **kwargs):
        """

        :param app:
        :param helper:
        :param helper_class:
        """
        app.config.setdefault("DATE_HELPER_COUNTRY", "IT")
        app.config.setdefault("DATE_HELPER_PROV", None)
        app.config.setdefault("DATE_HELPER_STATE", None)
        app.config.setdefault("DATE_PRETTY", "%d %B %Y %I:%M %p")
        app.config.setdefault("DATE_ISO_FORMAT", "%Y-%m-%dT%H:%M:%S")

        if helper is not None:
            self._helper = helper
        else:
            attrs = app.config.get_namespace('DATE_HELPER_')
            self._helper = helper_class(**attrs)

        self.iso_format = app.config.DATE_ISO_FORMAT
        if not hasattr(app, "extensions"):
            app.extensions = {}  # pragma: no cover
        app.extensions['date_helper'] = self

    def __getattr__(self, name):
        return getattr(self._helper, name)

    def to_iso_format(self, str_date, fmt=None, **kwargs):
        return self.change_format(str_date, in_fmt=fmt, out_fmt=self.iso_format, **kwargs)


date_helper = FlaskDateHelper()
