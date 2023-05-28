import flask

from .builder import Builder
from .encoders import JsonEncoder


class JsonBuilder(Builder):
    def __init__(self, mimetype: str, response_class=None, encoder=None, **kwargs):
        """

        :param mimetype:
        :param response_class:
        :param encoder:
        :param kwargs:
        """
        super().__init__(mimetype, response_class, **kwargs)
        self._encoder = encoder or JsonEncoder
        # it is necessary because jsonp uses another mimetype
        # and the object is instantiated once
        self._mimetype_backup = self._mimetype

    def _build(self, data, **kwargs):
        """

        :param data:
        :return:
        """
        # restore original mimetype at every response build
        self._mimetype = self._mimetype_backup

        if self.conf.get("DEBUG"):
            kwargs.setdefault("indent", self.conf.get("RB_DEFAULT_DUMP_INDENT"))
            kwargs.setdefault("separators", (", ", ": "))
        else:
            kwargs.setdefault("indent", None)
            kwargs.setdefault("separators", (",", ":"))

        kwargs.setdefault("cls", self._encoder)
        resp = self.to_json(data, **kwargs)

        param = self.conf.get("RB_JSONP_PARAM")
        if param:
            jsonp_callback = flask.request.args.get(param)
            if jsonp_callback and len(jsonp_callback) > 0:
                # backup and override original mimetype
                self._mimetype_backup = self._mimetype
                self._mimetype = "application/javascript"
                return "{}({});".format(jsonp_callback, resp)

        return resp

    @staticmethod
    def to_me(data: dict, **kwargs):
        """

        :param data:
        :return:
        """
        kwargs.setdefault("cls", JsonEncoder)
        return flask.json.dumps(data, **kwargs)

    @staticmethod
    def to_json(data, **kwargs):
        """

        :param data:
        :return:
        """
        return JsonBuilder.to_me(data, **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        """

        :param data:
        :return:
        """
        return flask.json.loads(data, **kwargs)
