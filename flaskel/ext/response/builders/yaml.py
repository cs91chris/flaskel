import io

import yaml

from .builder import Builder


class YamlBuilder(Builder):
    def _build(self, data, **kwargs):
        if self.conf.get("DEBUG"):
            kwargs.setdefault("indent", self.conf.get("RB_DEFAULT_DUMP_INDENT"))
        kwargs.setdefault("allow_unicode", self.conf.get("RB_YAML_ALLOW_UNICODE"))

        return YamlBuilder.to_yaml(data or {}, **kwargs)

    @staticmethod
    def to_me(data: dict, **kwargs):
        kwargs.setdefault("indent", 4)
        kwargs.setdefault("allow_unicode", True)
        kwargs.setdefault("default_flow_style", False)

        return yaml.safe_dump(data, **kwargs)

    @staticmethod
    def to_yaml(data, **kwargs):
        return YamlBuilder.to_me(data, **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        if isinstance(data, io.IOBase):
            return yaml.safe_load(data)
        return yaml.safe_load(io.StringIO(data))
