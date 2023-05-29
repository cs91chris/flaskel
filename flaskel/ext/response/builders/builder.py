from abc import ABC, abstractmethod

from flask import Response
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum


class Builder(ABC):
    def __init__(self, mimetype: str, response_class=None, **kwargs):
        if not isinstance(mimetype, str):
            raise TypeError(f"Invalid mimetype: {mimetype}")

        if response_class and not issubclass(response_class, Response):
            raise TypeError(
                f"Invalid response_class: {response_class}. "
                "You must extend flask Response class"
            )

        self.conf = kwargs
        self._mimetype = mimetype
        self._response_class = response_class or Response

        self._data = None
        self._headers = {HeaderEnum.CONTENT_TYPE: self.mimetype}

    @property
    def mimetype(self):
        return self._mimetype

    @property
    def data(self):
        return self._data

    @staticmethod
    @abstractmethod
    def to_dict(data, **kwargs):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_me(data, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def _build(self, data, **kwargs):
        raise NotImplementedError

    def build(self, data, **kwargs):
        self._data = self._build(data, **kwargs)
        return self.data

    def response(self, status=None, headers=None):
        headers = headers or {}
        ct = headers.get(HeaderEnum.CONTENT_TYPE)

        return self._response_class(
            self.data,
            mimetype=ct or self.mimetype,
            status=status or httpcode.SUCCESS,
            headers={**self._headers, **headers},
        )

    def transform(self, data, builder, inargs=None, outargs=None):
        _dict = builder.to_dict(data, **(inargs or {}))
        return self.build(_dict, **(outargs or {}))
