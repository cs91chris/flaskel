# from: https://github.com/quandyfactory/dicttoxml

import numbers
from collections.abc import Iterable


def get_xml_type(val):
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, str):
        return "str"
    if isinstance(val, int):
        return "int"
    if isinstance(val, float):
        return "float"
    if isinstance(val, numbers.Number):
        return "number"
    if isinstance(val, dict):
        return "dict"
    if isinstance(val, Iterable):
        return "list"

    return type(val).__name__


def escape_xml(s):
    if isinstance(s, str):
        s = s.replace("&", "&amp;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
    return s


def make_attr_string(value, attr_type):
    return f' type="{get_xml_type(value)}"' if attr_type else ""


def convert_kv(key, val, attr_string, cdata=False):
    if cdata is True:
        val = val.replace("]]>", "]]]]><![CDATA[>")
        content = "<![CDATA[" + val + "]]>"
    else:
        content = escape_xml(val)

    return f"<{key}{attr_string}>{content}</{key}>"


def convert(obj, attr_type, default_item_name, cdata):
    item_name = default_item_name
    attr_string = make_attr_string(obj, attr_type)

    if obj is None:
        return f"<{item_name}{attr_string}></{item_name}>"
    if isinstance(obj, bool):
        return f"<{item_name}{attr_string}>{str(obj).lower()}</{item_name}>"
    if isinstance(obj, (numbers.Number, str)):
        return convert_kv(item_name, obj, attr_string, cdata)
    if hasattr(obj, "isoformat"):
        return convert_kv(item_name, obj.isoformat(), attr_string, cdata)
    if isinstance(obj, dict):
        return convert_dict(obj, attr_type, default_item_name, cdata)
    if isinstance(obj, Iterable):
        return convert_list(obj, attr_type, default_item_name, cdata)

    raise TypeError(f"Unsupported data type: {obj} ({type(obj).__name__})")


def convert_dict(obj, attr_type, default_item_name, cdata):
    output = []

    for key, val in obj.items():
        attr_string = make_attr_string(val, attr_type)

        if val is None:
            output.append(f"<{key}{attr_string}></{key}>")
        elif isinstance(val, bool):
            output.append(f"<{key}{attr_string}>{str(val).lower()}</{key}>")
        elif isinstance(val, (numbers.Number, str)):
            output.append(convert_kv(key, val, attr_string, cdata))
        elif hasattr(val, "isoformat"):
            output.append(convert_kv(key, val.isoformat(), attr_string, cdata))
        elif isinstance(val, dict):
            content = convert_dict(val, attr_type, default_item_name, cdata)
            output.append(f"<{key}{attr_string}>{content}</{key}>")
        elif isinstance(val, Iterable):
            content = convert_list(val, attr_type, default_item_name, cdata)
            output.append(f"<{key}{attr_string}>{content}</{key}>")
        else:
            raise TypeError(f"Unsupported data type: {val} ({type(val).__name__})")

    return "".join(output)


def convert_list(items, attr_type, default_item_name, cdata):
    output = []
    item_name = default_item_name

    for item in items:
        attr_string = make_attr_string(item, attr_type)

        if isinstance(item, (numbers.Number, str)):
            output.append(convert_kv(item_name, item, attr_string, cdata))
        elif hasattr(item, "isoformat"):  # datetime
            output.append(convert_kv(item_name, item.isoformat(), attr_string, cdata))
        elif isinstance(item, bool):
            output.append(
                f"<{item_name}{attr_string}>{str(item).lower()}</{item_name}>"
            )
        elif isinstance(item, dict):
            content = convert_dict(item, attr_type, default_item_name, cdata)
            if not attr_type:
                output.append(f"<{item_name}>{content}</{item_name}>")
            else:
                output.append(f'<{item_name} type="dict">{content}</{item_name}>')
        elif isinstance(item, Iterable):
            content = convert_list(item, attr_type, default_item_name, cdata)
            if not attr_type:
                output.append(f"<{item_name} {attr_string}>{content}</{item_name}>")
            else:
                output.append(
                    f'<{item_name} type="list"{attr_string}>{content}</{item_name}>'
                )
        elif item is None:
            output.append(f"<{item_name}{attr_string}></{item_name}>")
        else:
            raise TypeError(f"Unsupported data type: {item} ({type(item).__name__})")

    return "".join(output)


def dicttoxml(
    obj,
    root=True,
    custom_root="root",
    xml_declaration=True,
    attr_type=True,
    default_item_name="item",
    cdata=False,
    encoding="utf-8",
):
    output = []
    if root is True:
        if xml_declaration is True:
            output.append(f'<?xml version="1.0" encoding="{encoding}" ?>')

        content = convert(obj, attr_type, default_item_name, cdata)
        output.append(f"<{custom_root}>{content}</{custom_root}>")
    else:
        output.append(convert(obj, attr_type, default_item_name, cdata))

    return "".join(output)
