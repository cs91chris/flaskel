import importlib
import string
from random import SystemRandom


def import_from_module(name):
    """

    :param name:
    :return:
    """
    mod, attr = name.split(":")
    module = importlib.import_module(mod)
    return getattr(module, attr)


def parse_value(v):
    """

    :param v:
    :return:
    """
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        if v.lower() in ("true", "false"):
            return v.lower() == "true"
    return v


def get_from_dict(d, k, default=None):
    """
    get a value from dict without raising exceptions

    :param d: dict
    :param k: key
    :param default: default value if k is missing
    :return: d[k] or default
    """
    if isinstance(d, dict):
        return d.get(k, default)
    return default


def to_int(n):
    """
    cast input to int if an error occurred returns None

    :param n: input
    :return: int or None
    """
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


def to_float(n):
    """
    cast input to float if an error occurred returns None

    :param n: input
    :return: float or None
    """
    try:
        return float(n)
    except (TypeError, ValueError):
        return None


def random_string(length, alphabet=string.printable):
    """

    :param length:
    :param alphabet:
    :return:
    """
    return "".join(SystemRandom().choice(alphabet) for _ in range(length))
