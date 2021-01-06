import enum


class HashableDict(dict):
    def __hash__(self):
        """

        :return:
        """
        return hash(tuple(sorted(self.items())))


class ObjectDict(dict):
    def __init__(self, d=None, **kwargs):
        """

        :param d: input dictionary
        """
        super().__init__()
        data = d or kwargs

        for k, v in data.items():
            if isinstance(v, dict):
                v = ObjectDict(v)
            elif isinstance(v, list):
                v = [
                    ObjectDict(i)
                    if type(i) is dict else i
                    for i in v
                ]

            self[k] = v

    def __getattr__(self, name):
        if name in self:
            return self[name]

    def __setattr__(self, name, value):
        if type(value) is dict:
            self[name] = ObjectDict(value)
        else:
            self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]


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
