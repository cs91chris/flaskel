from werkzeug.routing import BaseConverter, FloatConverter, UnicodeConverter


class ListConverter(BaseConverter):
    default_separator = "+"

    def __init__(self, map_name=None, sep=None):
        """

        :param map_name:
        :param sep:
        """
        super().__init__(map_name)
        self._sep = sep or self.default_separator

    def to_python(self, value):
        """

        :param value:
        :return:
        """
        return value.split(self._sep)

    def to_url(self, value):
        """

        :param value:
        :return:
        """
        return self._sep.join(BaseConverter.to_url(self, v) for v in value)


CONVERTERS = {
    "list": ListConverter,
    "str": UnicodeConverter,
    "decimal": FloatConverter,
}
