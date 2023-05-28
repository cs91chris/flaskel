import base64

from .builder import Builder


class Base64Builder(Builder):
    def _build(self, data, **kwargs):
        kwargs.setdefault("enc", self.conf.get("RB_DEFAULT_ENCODE"))

        return Base64Builder.to_base64(str(data or ""), **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        return None

    @staticmethod
    def to_me(data, **kwargs):
        enc = kwargs.pop("enc", None)
        dec = kwargs.pop("dec", True)

        d = base64.b64encode(data.encode(enc), **kwargs)
        return d.decode() if dec is True else d

    @staticmethod
    def from_base64(data: str, **kwargs):
        return base64.b64decode(data, **kwargs)

    @staticmethod
    def to_base64(data, **kwargs):
        return Base64Builder.to_me(data, **kwargs)
