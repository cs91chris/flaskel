from werkzeug.routing import BaseConverter, FloatConverter, UnicodeConverter


class ListConverter(BaseConverter):
    def __init__(self, map=None, sep=None):
        """

        :param map:
        :param sep:
        """
        super().__init__(map)
        self._sep = sep or '+'

    def to_python(self, value):
        """

        :param value:
        :return:
        """
        return value.split(self._sep)

    def to_url(self, values):
        """

        :param values:
        :return:
        """
        return self._sep.join(BaseConverter.to_url(self, v) for v in values)


CONVERTERS = {
    'list': ListConverter,
    'str': UnicodeConverter,
    'decimal': FloatConverter,
}
