from operator import itemgetter
from typing import Any, List, Sequence

from flask import current_app as cap
from vbcore.date_helper import DateHelper
from vbcore.types import AnyDateType, OptInt, OptStr


def or_na(item: Any) -> Any:
    if not item:
        return cap.config["NOT_AVAILABLE_DESC"]
    return item


def yes_or_no(item: Any) -> str:
    return "yes" if bool(item) else "no"


def reverse(s: Sequence) -> Sequence:
    return s[::-1]


def pretty_date(date: AnyDateType, fmt: OptStr = None) -> OptStr:
    fmt = fmt or cap.config["PRETTY_DATE"]
    if not date:
        return None

    if isinstance(date, str):
        return DateHelper.change_format(date, out_fmt=fmt) or None
    return DateHelper.date_to_str(date, fmt=fmt) or None


def order_by(
    data: List[dict],
    item: Any,
    descending: bool = False,
    silent: bool = True,
) -> List[dict]:
    try:
        return sorted(data, key=itemgetter(item), reverse=descending)
    except KeyError:
        if silent:
            return data
        raise


def truncate(data: str, n: int, at_least: int = 0, term: str = " ...") -> str:
    if len(data) - n > at_least:
        return f"{data[:n]}{term}"
    return data


def human_byte_size(size: int, max_index: OptInt = None) -> str:
    idx = 0
    scale = cap.config["HUMAN_FILE_SIZE_SCALE"]
    divider = cap.config["HUMAN_FILE_SIZE_DIVIDER"]
    max_index = max_index or len(scale)

    if size < divider:
        return f"{size} B"

    for _idx in range(0, max_index):
        idx = _idx
        size /= divider
        if size < divider:
            break

    return "{:.2f} {}".format(size, scale[idx])
