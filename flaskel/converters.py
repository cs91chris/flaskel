from werkzeug.routing import BaseConverter
from werkzeug.routing import UnicodeConverter
from werkzeug.routing import FloatConverter


class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(super().to_url(v) for v in values)


CONVERTERS = {
    'list': ListConverter,
    'str': UnicodeConverter,
    'decimal': FloatConverter,
}
