import xmltodict

from .builder import Builder
from .dicttoxml import dicttoxml


class XmlBuilder(Builder):
    def _build(self, data, **kwargs):
        return self.to_xml(
            data or {},
            custom_root=kwargs.pop("root", self.conf.get("RB_XML_ROOT")),
            cdata=self.conf.get("RB_XML_CDATA"),
            **kwargs,
        )

    @staticmethod
    def to_me(data, **kwargs):
        kwargs.setdefault("default_item_name", "ROW")
        return dicttoxml(data, **kwargs)

    @staticmethod
    def to_xml(data, **kwargs):
        return XmlBuilder.to_me(data, **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        return xmltodict.parse(data, **kwargs)
