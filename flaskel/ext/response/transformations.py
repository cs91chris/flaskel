from .builders import CsvBuilder, JsonBuilder, XmlBuilder, YamlBuilder


class Transformer:
    @staticmethod
    def transform(bf, bt, data, from_args=None, to_args=None):
        _dict = bf.to_dict(data, **(from_args or {}))
        return bt.to_me(_dict, **(to_args or {}))

    @staticmethod
    def json_to_xml(data: str, json_args=None, xml_args=None):
        return Transformer.transform(JsonBuilder, XmlBuilder, data, json_args, xml_args)

    @staticmethod
    def xml_to_json(data: str, xml_args=None, json_args=None):
        return Transformer.transform(XmlBuilder, JsonBuilder, data, xml_args, json_args)

    @staticmethod
    def json_to_yaml(data: str, json_args=None, yaml_args=None):
        return Transformer.transform(
            JsonBuilder, YamlBuilder, data, json_args, yaml_args
        )

    @staticmethod
    def yaml_to_json(data: str, yaml_args=None, json_args=None):
        return Transformer.transform(
            YamlBuilder, JsonBuilder, data, yaml_args, json_args
        )

    @staticmethod
    def xml_to_yaml(data: str, xml_args=None, yaml_args=None):
        return Transformer.transform(XmlBuilder, YamlBuilder, data, xml_args, yaml_args)

    @staticmethod
    def yaml_to_xml(data: str, yaml_args=None, xml_args=None):
        return Transformer.transform(YamlBuilder, XmlBuilder, data, yaml_args, xml_args)

    @staticmethod
    def csv_to_xml(data: str, csv_args=None, xml_args=None):
        return Transformer.transform(CsvBuilder, XmlBuilder, data, csv_args, xml_args)

    @staticmethod
    def xml_to_csv(data: str, xml_args=None, csv_args=None):
        return Transformer.transform(XmlBuilder, CsvBuilder, data, xml_args, csv_args)

    @staticmethod
    def csv_to_yaml(data: str, csv_args=None, yaml_args=None):
        return Transformer.transform(CsvBuilder, YamlBuilder, data, csv_args, yaml_args)

    @staticmethod
    def yaml_to_csv(data: str, yaml_args=None, csv_args=None):
        return Transformer.transform(YamlBuilder, CsvBuilder, data, yaml_args, csv_args)

    @staticmethod
    def csv_to_json(data: str, csv_args=None, json_args=None):
        return Transformer.transform(CsvBuilder, JsonBuilder, data, csv_args, json_args)

    @staticmethod
    def json_to_csv(data: str, json_args=None, csv_args=None):
        return Transformer.transform(JsonBuilder, CsvBuilder, data, json_args, csv_args)
