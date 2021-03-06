import enum

from flask import current_app as cap


class ConfigProxy:
    def __init__(self, key=None):
        self.key = key

    def __getattr__(self, item):
        obj = self._proxy() or {}
        if not isinstance(item, str):
            return obj.get(item)
        for i in item.split('.'):
            obj = obj.get(item)
        return obj

    def __call__(self, item=None, *args, **kwargs):
        if item is None:
            return self._proxy()
        return self.__getattr__(item)

    def __getitem__(self, item):
        if item is None:
            return self._proxy()
        return self.__getattr__(item)

    def _proxy(self):
        res = cap.config

        if self.key is None:
            return cap.config
        for c in self.key.split('.'):
            res = res.get(c) or {}

        return res or None

    def get(self, item=None):
        return self.__call__(item)


class ExtProxy:
    def __init__(self, name):
        self._name = name

    @property
    def extension(self):
        return cap.extensions[self._name]

    def __getattr__(self, item):
        return getattr(self.extension, item)

    def __call__(self, *args, **kwargs):
        return self.extension()

    def __getitem__(self, item):
        return self.extension[item]


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


class ObjectDict(dict):
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            self[k] = self.normalize(v)

    def __dict__(self):
        data = {}
        for k, v in self.items():
            if isinstance(v, ObjectDict):
                data[k] = v.__dict__()
            elif isinstance(v, list):
                data[k] = [i.__dict__() for i in v]
            else:
                data[k] = v

        return data

    def __getstate__(self):
        return self.__dict__()

    def __setstate__(self, state):
        for k, v in state.items():
            self.__setattr__(k, v)

    def __getattr__(self, name):
        if name in self:
            return self[name]

    def __setattr__(self, name, value):
        self[name] = self.normalize(value)

    def __delattr__(self, name):
        if name in self:
            del self[name]

    @staticmethod
    def normalize(data):
        try:
            if isinstance(data, (list, tuple, set)):
                return [
                    ObjectDict(**r) if isinstance(r, dict) else r
                    for r in data
                ]
            return ObjectDict(**data)
        except (TypeError, ValueError, AttributeError):
            return data


class IntEnum(enum.IntEnum):
    @classmethod
    def to_list(cls):
        return [
            ObjectDict(id=getattr(cls, m).value, label=getattr(cls, m).name)
            for m in cls.__members__
        ]

    def to_dict(self):
        return ObjectDict(id=self.value, label=self.name)

    def __repr__(self):
        return f"<{self.value}: {self.name}>"

    def __str__(self):
        return self.name
