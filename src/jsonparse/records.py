"""JSON transforms and local record interchange, using only the standard library."""

import copy
import csv
import io
import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any, Dict, Iterator, List, Optional, Union


_MISSING = object()


def _pointer_tokens(pointer: str) -> List[str]:
    if not isinstance(pointer, str):
        raise TypeError("JSON pointer must be a string")
    if pointer == "":
        return []
    if not pointer.startswith("/") or re.search(r"~(?:[^01]|$)", pointer):
        raise ValueError("invalid JSON pointer; use slash-prefixed tokens and ~0/~1 escapes")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def json_pointer(obj: Any, pointer: str, *, default: Any = _MISSING) -> Any:
    """Resolve an RFC 6901 string pointer (not a URI fragment).

    The empty pointer selects the root. Missing keys, invalid array indexes,
    and incompatible types raise KeyError, unless an explicit default is given.
    Malformed pointer syntax always raises ValueError. The result is a reference
    to the selected value, matching json_get/json_query's lookup behavior.
    """
    current = obj
    for token in _pointer_tokens(pointer):
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            # Compare lengths before int conversion so huge indexes fail normally.
            if len(token) <= len(str(len(current))) and int(token) < len(current):
                current = current[int(token)]
                continue
            current = _MISSING
        else:
            current = _MISSING
        if current is _MISSING:
            if default is not _MISSING:
                return default
            raise KeyError("JSON pointer does not resolve")
    return current


def _validate_json(value: Any) -> None:
    # The encoder detects cycles and nonfinite numbers before iterative traversal.
    json.dumps(value, allow_nan=False)
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise TypeError("JSON object keys must be strings")
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise TypeError("expected JSON-compatible values")


def json_flatten(obj: Any) -> Dict[str, Any]:
    """Map RFC 6901 pointers to leaves, preserving nulls and empty containers.

    Arrays use numeric index tokens; object keys are escaped. Empty containers
    and scalar roots map to the empty pointer. This is not an invertible format:
    a numeric object key and an array index can have the same pointer spelling.
    Inputs must contain only finite JSON values; cycles are rejected.
    """
    _validate_json(obj)
    result: Dict[str, Any] = {}
    pending = [("", obj)]
    while pending:
        path, value = pending.pop()
        if isinstance(value, dict) and value:
            children = [(path + "/" + key.replace("~", "~0").replace("/", "~1"), child)
                        for key, child in value.items()]
            pending.extend(reversed(children))
        elif isinstance(value, list) and value:
            pending.extend(reversed([(path + "/" + str(i), child) for i, child in enumerate(value)]))
        else:
            result[path] = copy.deepcopy(value)
    return result


def json_merge_patch(target: Any, patch: Any) -> Any:
    """Apply RFC 7396 merge semantics to finite JSON values without mutating inputs.

    Object members merge recursively; null members delete keys. A non-object
    patch replaces the entire target, including arrays. The result owns its data.
    """
    _validate_json(target)
    _validate_json(patch)

    def merge(original: Any, changes: Any) -> Any:
        if not isinstance(changes, dict):
            return copy.deepcopy(changes)
        result = copy.deepcopy(original) if isinstance(original, dict) else {}
        for key, value in changes.items():
            if value is None:
                result.pop(key, None)
            else:
                result[key] = merge(result.get(key), value)
        return result

    return merge(target, patch)


def json_project(records: Iterable, fields: Mapping, *, default: Any = None) -> List[Dict[str, Any]]:
    """Rename/select columns from object records using output-name → JSON pointer.

    Missing paths receive a copy of default; explicit null remains null. Each
    result is independent of the input and other rows. Field syntax is validated
    even for empty inputs. Use json_query first to select the input record array.
    """
    if not isinstance(fields, Mapping) or any(not isinstance(key, str) for key in fields):
        raise TypeError("fields must map string names to JSON pointers")
    for pointer in fields.values():
        _pointer_tokens(pointer)
    result = []
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("each record must be a JSON object")
        result.append({name: copy.deepcopy(json_pointer(record, pointer, default=default))
                       for name, pointer in fields.items()})
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("JSON must not contain NaN or Infinity")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON number exceeds the supported finite range")
    return number


def _strict_loads(text: str) -> Any:
    return json.loads(text, parse_constant=_reject_constant, parse_float=_finite_float)


def iter_jsonl(source: Union[str, Iterable], *, skip_blank: bool = False) -> Iterator[Any]:
    """Yield JSON values from a string or iterable of text lines, without closing it.

    Streams are consumed lazily. Blank lines are errors unless skip_blank=True.
    UTF-8 BOMs and nonfinite numbers are rejected. Errors identify the 1-based
    physical line number without echoing its contents. This function does no I/O
    itself; callers open their own text streams with UTF-8 encoding.
    """
    lines = io.StringIO(source) if isinstance(source, str) else source
    for number, line in enumerate(lines, 1):
        if not isinstance(line, str):
            raise TypeError("JSON Lines source must yield text lines")
        if skip_blank and not line.strip():
            continue
        try:
            yield _strict_loads(line)
        except ValueError:
            raise ValueError(f"invalid JSON Lines record at line {number}") from None


def jsonl_dumps(records: Iterable) -> str:
    """Serialize finite JSON values as UTF-8-encodable JSON Lines, ending in LF."""
    lines = []
    for record in records:
        _validate_json(record)
        lines.append(json.dumps(record, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n")
    output = "".join(lines)
    output.encode("utf-8")  # Reject lone surrogates before returning invalid UTF-8 text.
    return output


def _delimiter(value: str) -> str:
    if not isinstance(value, str) or len(value) != 1 or value in '\r\n"\0':
        raise ValueError("delimiter must be one character other than quote, newline or NUL")
    return value


def _csv_cell(value: Any, escape_formulas: bool) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        if escape_formulas and (value.startswith(("\t", "\r", "\n")) or
                                value.lstrip().startswith(("=", "+", "-", "@"))):
            return "'" + value
        return value
    _validate_json(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def records_to_csv(records: Iterable, *, fieldnames: Optional[Iterable] = None,
                   delimiter: str = ",", escape_formulas: bool = True) -> str:
    """Serialize object records with CRLF rows, quoting and first-seen union columns.

    Explicit fieldnames select/order columns. Null/missing values become empty
    cells; nested values become compact JSON. Formula-like strings (including
    headings) receive an apostrophe by default; this changes their value, is not
    a universal spreadsheet security guarantee, and can be disabled for trusted
    machine interchange. Numeric negatives are not escaped. Materializes rows.
    """
    separator = _delimiter(delimiter)
    if isinstance(fieldnames, (str, bytes)):
        raise TypeError("fieldnames must be an iterable of names, not a string")
    rows = list(records)
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(key, str) for key in row):
            raise TypeError("CSV records must be objects with string keys")
    names = list(fieldnames) if fieldnames is not None else list(dict.fromkeys(key for row in rows for key in row))
    if any(not isinstance(name, str) for name in names):
        raise TypeError("CSV field names must be strings")
    if len(set(names)) != len(names):
        raise ValueError("CSV field names must be unique")
    headings = [_csv_cell(name, escape_formulas) for name in names]
    if len(set(headings)) != len(headings):
        raise ValueError("CSV field names collide after formula escaping")
    if not names:
        return ""
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=separator, lineterminator="\r\n")
    writer.writerow(headings)
    for row in rows:
        writer.writerow([_csv_cell(row.get(name), escape_formulas) for name in names])
    return output.getvalue()


def csv_to_records(text: str, *, delimiter: str = ",") -> List[Dict[str, str]]:
    """Read header-based CSV into string-valued records; never infer data types.

    Accepts a leading BOM and quoted newlines. Duplicate headers, ragged rows,
    and csv.reader strict-mode errors fail explicitly. Quotes inside unquoted
    cells are literal, per the stdlib parser. Blank physical rows are ignored.
    Formula-escape apostrophes are preserved, not silently removed.
    """
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""), delimiter=_delimiter(delimiter), strict=True)
    try:
        headers = next((row for row in reader if row), None)
        if headers is None:
            return []
        if len(set(headers)) != len(headers):
            raise ValueError("CSV header names must be unique")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(headers):
                raise ValueError(f"CSV column count mismatch at line {reader.line_num}")
            rows.append(dict(zip(headers, row)))
        return rows
    except csv.Error:
        raise ValueError(f"invalid CSV at line {reader.line_num}") from None


__all__ = ["json_pointer", "json_flatten", "json_merge_patch", "json_project",
           "iter_jsonl", "jsonl_dumps", "records_to_csv", "csv_to_records"]
