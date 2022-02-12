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
