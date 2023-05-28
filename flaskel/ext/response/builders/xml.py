import xmltodict

from .builder import Builder
from .dicttoxml import DictToXML


class XmlBuilder(Builder):
    def _build(self, data, **kwargs):
        """

        :param data:
        :return:
        """
        return self.to_xml(
            data or {},
            custom_root=kwargs.pop("root", self.conf.get("RB_XML_ROOT")),
            cdata=self.conf.get("RB_XML_CDATA"),
            **kwargs,
        )

    @staticmethod
    def to_me(data, **kwargs):
        """

        :param data:
        :return:
        """
        kwargs.setdefault("item_func", lambda x: "ROW")
        return DictToXML().dicttoxml(data, **kwargs)

    @staticmethod
    def to_xml(data, **kwargs):
        """

        :param data:
        :return:
        """
        return XmlBuilder.to_me(data, **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        """

        :param data:
        :return:
        """
        return xmltodict.parse(data, **kwargs)
