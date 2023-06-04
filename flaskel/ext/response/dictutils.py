from collections.abc import MutableMapping


def to_flatten(data, to_dict=None, **kwargs):
    kwargs.setdefault("sep", "_")
    kwargs.setdefault("parent_key", "")

    def _flatten_dict(d, parent_key, sep):
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
    to_dict = to_dict or dict

    if not isinstance(data, (list, tuple)):
        data = (data,)

    for item in data:
        zipkeys = {}
        try:
            item = _flatten_dict(to_dict(item), **kwargs)
        except TypeError as exc:
            raise TypeError(
                f"Could not convert '{item}' into dict object, "
                f"please provide a to_dict function"
            ) from exc

        for key in list(item.keys()):
            if isinstance(item.get(key), list):
                if len(item.get(key)) > 0:
                    zipkeys.update({key: item.get(key)})
                    del item[key]

        _sep = kwargs.get("sep")
        for zk, value in zipkeys.items():
            for i in value:
                response.append({**item, **{f"{zk}{_sep}{k}": v for k, v in i.items()}})

        if len(zipkeys.keys()) == 0:
            response.append(item)
    return response
