# from: https://github.com/quandyfactory/dicttoxml

import collections.abc
import numbers
from random import randint
from xml.dom.minidom import parseString


class DictToXML:
    def __init__(self, declaration=None):
        self._ids = []
        self._declaration = declaration or '<?xml version="1.0" encoding="UTF-8" ?>'

    @staticmethod
    def _make_id(element, start=100000, end=999999):
        return "%s_%s" % (element, randint(start, end))

    def get_unique_id(self, element):
        """Returns a unique id for a given element"""
        this_id = self._make_id(element)
        dup = True
        while dup:
            if this_id not in self._ids:
                dup = False
                self._ids.append(this_id)
            else:
                this_id = self._make_id(element)
        return self._ids[-1]

    @staticmethod
    def get_xml_type(val):
        """Returns the data type for the xml type attribute"""
        return val.__class__.__name__

    @staticmethod
    def escape_xml(s):
        try:
            return (
                s.replace("&", "&amp;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
        except AttributeError:
            return s

    @staticmethod
    def _make_attr_string(attr):
        """Returns an attribute string in the form key="val" """
        attr_string = " ".join(['%s="%s"' % (k, v) for k, v in attr.items()])
        return "%s%s" % (" " if attr_string != "" else "", attr_string)

    def key_is_valid_xml(self, key):
        """Checks that a key is a valid XML name"""
        # noinspection PyBroadException
        try:
            parseString("%s<%s>foo</%s>" % (self._declaration, key, key))
        except Exception:  # minidom does not implement exceptions well
            return False
        return True

    def make_valid_xml_name(self, key, attr):
        """Tests an XML name and fixes it if invalid"""
        key = self.escape_xml(key)
        attr = self.escape_xml(attr)

        # pass through if key is already valid
        if self.key_is_valid_xml(key):
            return key, attr
        # prepend a lowercase n if the key is numeric
        if key.isdigit():
            return "n%s" % key, attr
        # replace spaces with underscores if that fixes the problem
        if self.key_is_valid_xml(key.replace(" ", "_")):
            return key.replace(" ", "_"), attr

        attr["name"] = key
        return "key", attr

    @staticmethod
    def wrap_cdata(s):
        """Wraps a string into CDATA sections"""
        return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"

    def convert(self, obj, ids, attr_type, item_func, cdata, parent="root"):
        """Routes the elements of an object to the right function to convert them
        based on their data type"""
        item_name = item_func(parent)

        if isinstance(obj, numbers.Number) or type(obj) is str:
            return self.convert_kv(item_name, obj, attr_type, cdata)
        if hasattr(obj, "isoformat"):
            return self.convert_kv(item_name, obj.isoformat(), attr_type, cdata)
        if type(obj) is bool:
            return self.convert_bool(item_name, obj, attr_type, cdata)
        if obj is None:
            return self.convert_none(item_name, "", attr_type, cdata)
        if isinstance(obj, dict):
            return self.convert_dict(obj, ids, parent, attr_type, item_func, cdata)
        if isinstance(obj, collections.abc.Iterable):
            return self.convert_list(obj, ids, parent, attr_type, item_func, cdata)

        raise TypeError("Unsupported data type: %s (%s)" % (obj, type(obj).__name__))

    def convert_dict(self, obj, ids, parent, attr_type, item_func, cdata):
        """Converts a dict into an XML string."""
        output = []
        for key, val in obj.items():
            attr = {} if not ids else {"id": "%s" % (self.get_unique_id(parent))}
            key, attr = self.make_valid_xml_name(key, attr)

            if isinstance(val, numbers.Number) or type(val) is str:
                output.append(self.convert_kv(key, val, attr_type, attr, cdata))
            elif hasattr(val, "isoformat"):  # datetime
                output.append(
                    self.convert_kv(key, val.isoformat(), attr_type, attr, cdata)
                )
            elif type(val) is bool:
                output.append(self.convert_bool(key, val, attr_type, attr, cdata))
            elif isinstance(val, dict):
                if attr_type:
                    attr["type"] = self.get_xml_type(val)
                output.append(
                    "<%s%s>%s</%s>"
                    % (
                        key,
                        self._make_attr_string(attr),
                        self.convert_dict(val, ids, key, attr_type, item_func, cdata),
                        key,
                    )
                )
            elif isinstance(val, collections.abc.Iterable):
                if attr_type:
                    attr["type"] = self.get_xml_type(val)
                output.append(
                    "<%s%s>%s</%s>"
                    % (
                        key,
                        self._make_attr_string(attr),
                        self.convert_list(val, ids, key, attr_type, item_func, cdata),
                        key,
                    )
                )
            elif val is None:
                output.append(self.convert_none(key, val, attr_type, attr, cdata))
            else:
                raise TypeError(
                    "Unsupported data type: %s (%s)" % (val, type(val).__name__)
                )

        return "".join(output)

    def convert_list(self, items, ids, parent, attr_type, item_func, cdata):
        """Converts a list into an XML string."""
        this_id = None
        output = []
        item_name = item_func(parent)
        if ids:
            this_id = self.get_unique_id(parent)

        for i, item in enumerate(items):
            attr = {} if not ids else {"id": "%s_%s" % (this_id, i + 1)}
            if isinstance(item, numbers.Number) or type(item) is str:
                output.append(self.convert_kv(item_name, item, attr_type, attr, cdata))
            elif hasattr(item, "isoformat"):  # datetime
                output.append(
                    self.convert_kv(item_name, item.isoformat(), attr_type, attr, cdata)
                )
            elif type(item) is bool:
                output.append(
                    self.convert_bool(item_name, item, attr_type, attr, cdata)
                )
            elif isinstance(item, dict):
                value = self.convert_dict(
                    item, ids, parent, attr_type, item_func, cdata
                )
                tag = "<%s>%s</%s>" if not attr_type else '<%s type="dict">%s</%s>'
                output.append(tag % (item_name, value, item_name))
            elif isinstance(item, collections.abc.Iterable):
                tag = "<%s %s>%s</%s>" if not attr_type else '<%s type="list"%s>%s</%s>'
                output.append(
                    tag
                    % (
                        item_name,
                        self._make_attr_string(attr),
                        self.convert_list(
                            item, ids, item_name, attr_type, item_func, cdata
                        ),
                        item_name,
                    )
                )
            elif item is None:
                output.append(
                    self.convert_none(item_name, None, attr_type, attr, cdata)
                )
            else:
                raise TypeError(
                    "Unsupported data type: %s (%s)" % (item, type(item).__name__)
                )

        return "".join(output)

    def convert_kv(self, key, val, attr_type, attr=None, cdata=False):
        """Converts a number or string into an XML element"""
        attr = attr or {}
        key, attr = self.make_valid_xml_name(key, attr)
        if attr_type:
            attr["type"] = self.get_xml_type(val)

        return "<%s%s>%s</%s>" % (
            key,
            self._make_attr_string(attr),
            self.wrap_cdata(val) if cdata is True else self.escape_xml(val),
            key,
        )

    # noinspection PyUnusedLocal
    def convert_bool(self, key, val, attr_type, attr=None, cdata=False):
        """Converts a boolean into an XML element"""
        attr = attr or {}
        key, attr = self.make_valid_xml_name(key, attr)
        if attr_type:
            attr["type"] = self.get_xml_type(val)

        attr_string = self._make_attr_string(attr)
        return "<%s%s>%s</%s>" % (key, attr_string, str(val).lower(), key)

    # noinspection PyUnusedLocal
    def convert_none(self, key, val, attr_type, attr=None, cdata=False):
        """Converts a null value into an XML element"""
        attr = attr or {}
        key, attr = self.make_valid_xml_name(key, attr)
        if attr_type:
            attr["type"] = self.get_xml_type(val)

        return "<%s%s></%s>" % (key, self._make_attr_string(attr), key)

    def dicttoxml(
        self,
        obj,
        root=True,
        custom_root="root",
        ids=False,
        attr_type=True,
        item_func=lambda p: "item",
        cdata=False,
        encoding="utf-8",
    ):
        """Converts a python object into XML.
        Arguments:
            - root specifies whether the output is wrapped in an XML root element
              Default is True
            - custom_root allows you to specify a custom root element.
              Default is 'root'
            - ids specifies whether elements get unique ids.
              Default is False
            - attr_type specifies whether elements get a data type attribute.
              Default is True
            - item_func specifies what function should generate the element name for
              items in a list.
              Default is 'item'
            - cdata specifies whether string values should be wrapped in CDATA sections.
              Default is False
        """
        output = []
        if root is True:
            output.append(self._declaration)
            output.append(
                "<%s>%s</%s>"
                % (
                    custom_root,
                    self.convert(
                        obj, ids, attr_type, item_func, cdata, parent=custom_root
                    ),
                    custom_root,
                )
            )
        else:
            output.append(
                self.convert(obj, ids, attr_type, item_func, cdata, parent="")
            )
        return "".join(output).encode(encoding)
