import typing as t
from dataclasses import dataclass
from math import ceil

from flask import current_app as cap


class ConfigProxy:
    def __init__(self, key: t.Optional[str] = None, default=None):
        self.__key = key
        self.__default = default

    def __getattr__(self, item):
        obj = self._proxy()
        if obj == self.__default:
            return self.__default
        if not isinstance(item, str):
            return obj.get(item)
        for i in item.split("."):
            obj = obj.get(i)
        return obj

    def __call__(self, item: t.Optional[str] = None, **kwargs):
        return self.__getitem__(item)

    def __getitem__(self, item: t.Optional[str] = None):
        if item is None:
            return self._proxy()
        return self.__getattr__(item)

    def _proxy(self):
        res = cap.config

        if self.__key is None:
            return cap.config

        if "." not in self.__key:
            res = res.get(self.__key, self.__default)
        else:
            for key in self.__key.split("."):
                res = res.get(key, {})

        return res if res is not None else self.__default

    def get(self, item: t.Optional[str] = None):
        res = self(item)
        return res if res is not None else self.__default


class ExtProxy:
    def __init__(self, name: str):
        self._name = name

    @property
    def extension(self):
        attrs = self._name.split(".")
        ret = cap.extensions[attrs[0]]
        for a in attrs[1:]:
            ret = getattr(ret, a, None)

        return ret

    def __getattr__(self, item):
        return getattr(self.extension, item)

    def __call__(self, *args, **kwargs):
        return self.extension()

    def __getitem__(self, item: str):
        return self.extension[item]


@dataclass(frozen=True)
class Pagination:
    page: t.Optional[int] = None
    page_size: t.Optional[int] = None
    max_page_size: t.Optional[int] = None

    def is_paginated(self, total: int) -> bool:
        return (self.page or 1) < self.pages(total)

    def pages(self, total: int) -> int:
        page_size = self.per_page()
        return int(ceil(total / page_size)) if page_size else 0

    def offset(self) -> int:
        if not self.page:
            return 0
        return (self.page - 1) * self.per_page()

    def per_page(self) -> int:
        if self.page_size:
            if self.max_page_size:
                return min(self.page_size, self.max_page_size)
            return self.page_size
        return self.max_page_size
