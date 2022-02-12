from vbcore.date_helper import DateHelper


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

    def init_app(self, app, helper=DateHelper, **__):
        """

        :param app:
        :param helper:
        """
        app.config.setdefault("DATE_HELPER_COUNTRY", "IT")
        app.config.setdefault("DATE_HELPER_PROV", None)
        app.config.setdefault("DATE_HELPER_STATE", None)
        app.config.setdefault("DATE_PRETTY", helper.DATE_PRETTY_FORMAT)
        app.config.setdefault("DATE_ISO_FORMAT", helper.DATE_ISO_FORMAT)

        self._helper = helper
        self.iso_format = app.config.DATE_ISO_FORMAT

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["date_helper"] = self

    def __getattr__(self, name):
        return getattr(self._helper, name)

    def to_iso_format(self, str_date, fmt=None, **kwargs):
        return self.change_format(
            str_date, in_fmt=fmt, out_fmt=self.iso_format, **kwargs
        )


date_helper = FlaskDateHelper()
