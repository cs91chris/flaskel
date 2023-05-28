import datetime
import uuid
from collections import Counter, defaultdict, deque, OrderedDict
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace

from flask import json

try:
    # noinspection PyUnresolvedReferences
    from bson import ObjectId

    object_id = ObjectId  # type: ignore
except ImportError:
    object_id = str  # type: ignore


class SetsEncoderMixin(json.JSONEncoder):
    """
    Encoders for: set, frozenset
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, (set, frozenset)):
            return list(o)

        return super().default(o)


class BytesEncoderMixin(json.JSONEncoder):
    """
    Encoders for: bytes, bytearray
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, (bytes, bytearray)):
            return o.decode()

        return super().default(o)


class BuiltinEncoderMixin(BytesEncoderMixin, SetsEncoderMixin):
    """
    Encoders for: Enum, Decimal
    Extends: BytesEncoderMixin, SetsEncoderMixin
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, Decimal):
            return float(o)

        return super().default(o)


class DateTimeEncoderMixin(json.JSONEncoder):
    """
    Encoders for: datetime, date, time, timedelta
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        if isinstance(o, datetime.timedelta):
            return o.total_seconds()

        return super().default(o)


class TypesEncoderMixin(json.JSONEncoder):
    """
    Encoders for: types
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, SimpleNamespace):
            return o.__dict__

        return super().default(o)


class CollectionsEncoderMixin(json.JSONEncoder):
    """
    Encoders for: collections
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, deque):
            return list(o)
        if isinstance(o, (defaultdict, OrderedDict, Counter)):
            return dict(o)
        try:
            # check for namedtuple compliant
            # noinspection PyProtectedMember
            return o._asdict()
        except (AttributeError, TypeError):
            pass

        return super().default(o)


class ExtraEncoderMixin(json.JSONEncoder):
    """
    Encoders for: UUID, ObjectId and object with methods: to_dict, asdict
    """

    def default(self, o, *args, **kwargs):
        if isinstance(o, uuid.UUID):
            return o.hex
        if isinstance(o, object_id):
            return str(o)
        try:
            return o.asdict()
        except (AttributeError, TypeError):
            pass
        try:
            return o.to_dict()
        except (AttributeError, TypeError):
            pass

        return super().default(o)


class JsonEncoder(
    BuiltinEncoderMixin,
    DateTimeEncoderMixin,
    TypesEncoderMixin,
    CollectionsEncoderMixin,
    ExtraEncoderMixin,
):
    """
    Extends all encoders provided with this module
    """

    def default(self, o, *args, **kwargs):
        return super().default(o)
