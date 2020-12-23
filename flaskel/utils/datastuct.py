class HashableDict(dict):
    def __hash__(self):
        """

        :return:
        """
        return hash(tuple(sorted(self.items())))


class ObjectDict(dict):
    def __init__(self, d):
        """

        :param d: input dictionary
        """
        super().__init__()

        for k, v in d.items():
            if isinstance(v, dict):
                v = ObjectDict(v)
            elif isinstance(v, list):
                v = [ObjectDict(i) if type(i) is dict else i for i in v]

            self[k] = v

    def __getattr__(self, name):
        """

        :param name:
        :return:
        """
        if name in self:
            return self[name]

    def __setattr__(self, name, value):
        """

        :param name:
        :param value:
        """
        if type(value) is dict:
            self[name] = ObjectDict(value)
        else:
            self[name] = value

    def __delattr__(self, name):
        """

        :param name:
        """
        if name in self:
            del self[name]
