import enum


class HashableDict(dict):
    def __hash__(self):
        """

        :return:
        """
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
        except (TypeError, AttributeError):
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
