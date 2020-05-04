import importlib


def import_from_module(name):
    """

    :param name:
    :return:
    """
    mod, attr = name.split(':')
    module = importlib.import_module(mod)
    return getattr(module, attr)
