from collections.abc import MutableMapping


def rename_keys(data, trans=None, **kwargs):
    """

    :param data:
    :param trans:
    :param kwargs:
    """
    if trans is None:
        for k, v in kwargs.items():
            data[v] = data.pop(k)
    else:
        for k in list(data.keys()):
            data[trans(k)] = data.pop(k)

    return data


def to_flatten(data, to_dict=None, **kwargs):
    """

    :param data:
    :param to_dict:
    :return:
    """
    kwargs.setdefault("sep", "_")
    kwargs.setdefault("parent_key", "")

    def _flatten_dict(d, parent_key, sep):
        """

        :param d:
        :param parent_key:
        :param sep:
        :return:
        """
        items = []

        for k, v in d.items():
            nk = (parent_key + sep + k) if parent_key else k

            if isinstance(v, MutableMapping):
                fdict = _flatten_dict(v, nk, sep=sep)
                items.extend(fdict.items())
            else:
                items.append((nk, v))
        return dict(items)

    response = []
    to_dict = to_dict or (lambda x: dict(x))

    if not isinstance(data, (list, tuple)):
        data = (data,)

    for item in data:
        zipkeys = {}
        try:
            item = _flatten_dict(to_dict(item), **kwargs)
        except TypeError:
            raise TypeError(
                "Could not convert '%s' into dict object, "
                "please provide a to_dict function",
                item,
            )

        for key in list(item.keys()):
            if isinstance(item.get(key), list):
                if len(item.get(key)) > 0:
                    zipkeys.update({key: item.get(key)})
                    del item[key]

        sep = kwargs.get("sep")
        for zk, value in zipkeys.items():
            pk = "{}{}".format(zk, sep)
            for i in value:
                response.append(
                    {**item, **{"{}{}".format(pk, k): v for k, v in i.items()}}
                )

        if len(zipkeys.keys()) == 0:
            response.append(item)
    return response
