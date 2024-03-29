from vbcore.date_helper import DateHelper, DateTimeFmt


class FlaskDateHelper:
    def __init__(self, app=None, **kwargs):
        self._helper = None
        self.iso_format = None

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, helper=DateHelper, **__):
        app.config.setdefault("DATE_HELPER_COUNTRY", "IT")
        app.config.setdefault("DATE_HELPER_PROV", None)
        app.config.setdefault("DATE_HELPER_STATE", None)
        app.config.setdefault("DATE_PRETTY", DateTimeFmt.PRETTY)
        app.config.setdefault("DATE_ISO_FORMAT", DateTimeFmt.ISO)

        self._helper = helper
        self.iso_format = app.config.DATE_ISO_FORMAT

        app.extensions["date_helper"] = self

    def __getattr__(self, name):
        return getattr(self._helper, name)
