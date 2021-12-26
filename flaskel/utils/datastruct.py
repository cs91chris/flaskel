import enum

from flask import current_app as cap


class ConfigProxy:
    def __init__(self, key=None, default=None):
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

    def __call__(self, item=None, **kwargs):
        return self.__getitem__(item)

    def __getitem__(self, item):
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

    def get(self, item=None):
        res = self.__call__(item)
        return res if res is not None else self.__default


class ExtProxy:
    def __init__(self, name):
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
                data[k] = []
                for i in v:
                    data[k].append(i.__dict__() if hasattr(i, "__dict__") else i)
            else:
                data[k] = v

        return data

    def __getstate__(self):
        return self.__dict__()  # pylint: disable=not-callable

    def __setstate__(self, state):
        for k, v in state.items():
            self.__setattr__(k, v)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        return None

    def __setattr__(self, name, value):
        self[name] = self.normalize(value)

    def __delattr__(self, name):
        if name in self:
            del self[name]

    def patch(self, __dict, **kwargs):
        """

        :param __dict:
        :param kwargs:
        :return:
        """
        super().update(__dict, **kwargs)
        return self

    @staticmethod
    def normalize(data):
        """

        :param data:
        :return:
        """
        try:
            if isinstance(data, (list, tuple, set)):
                return [ObjectDict(**r) if isinstance(r, dict) else r for r in data]
            return ObjectDict(**data)
        except (TypeError, ValueError, AttributeError):
            return data

    def get_namespace(self, prefix, lowercase=True, trim=True):
        """
        Returns a dictionary containing a subset of configuration options
        that match the specified prefix.

        :param prefix: a configuration prefix
        :param lowercase: a flag indicating if the keys should be lowercase
        :param trim: a flag indicating if the keys should include the namespace
        """
        res = {}
        for k, v in self.items():
            if k.startswith(prefix):
                key = k[len(prefix) :] if trim else k
                res[key.lower() if lowercase else key] = v
        return res


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


class Dumper:
    def __init__(self, data, *args, callback=None, **kwargs):
        """

        :param data:
        :param callback:
        :param args:
        :param kwargs:
        """
        self.data = data
        self._args = args
        self._kwargs = kwargs
        self._callback = callback

    def dump(self):
        if self._callback is not None:
            return self._callback(self.data, *self._args, **self._kwargs)
        return str(self.data)

    def __str__(self):
        return self.dump()
