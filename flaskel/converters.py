import typing as t
from decimal import Decimal

from werkzeug.routing import BaseConverter, FloatConverter, Map, UnicodeConverter


class ListConverter(BaseConverter):
    def __init__(self, map_name: Map, sep: str = "+"):
        """

        :param map_name:
        :param sep:
        """
        super().__init__(map_name)
        self._sep = sep

    def to_python(self, value: str) -> t.List[str]:
        """

        :param value:
        :return:
        """
        return value.split(self._sep)

    def to_url(self, value: t.List[str]) -> str:
        """

        :param value:
        :return:
        """
        return super().to_url(self._sep.join(value))


class DecimalConverter(FloatConverter):
    num_convert = Decimal  # type: ignore

    def __init__(
        self,
        map_name: "Map",
        min: t.Optional[float] = None,  # pylint: disable=redefined-builtin
        max: t.Optional[float] = None,  # pylint: disable=redefined-builtin
        signed: bool = True,
    ) -> None:
        super().__init__(map_name, min=min, max=max, signed=signed)


CONVERTERS = {
    "list": ListConverter,
    "str": UnicodeConverter,
    "decimal": DecimalConverter,
}
