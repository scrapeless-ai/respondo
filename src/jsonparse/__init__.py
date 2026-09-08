"""
JSON Utilities Module

Provides JSON parsing, extraction, and safe nested access.
No external dependencies - uses stdlib only (json).
"""

import json
import re
from typing import Any, List

from .records import (
    csv_to_records, iter_jsonl, json_flatten, json_merge_patch, json_pointer,
    json_project, jsonl_dumps, records_to_csv,
)


_WILDCARD = object()
_QUERY_KEY = re.compile(r"[^.\[\]\s*$]+")
_QUERY_BRACKET = re.compile(
    r'''\[\s*(?:(-?\d+)|(\*)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'))\s*\]'''
)


def _quoted_query_key(key: str) -> str:
    if key.startswith('"'):
        return json.loads(key)
    # Convert the single-quoted spelling to a JSON string, retaining JSON
    # escapes (including surrogate pairs) and allowing an escaped apostrophe.
    parts: List[str] = []
    position = 1
    while position < len(key) - 1:
        character = key[position]
        if character == "\\":
            position += 1
            escaped = key[position]
            parts.append("'" if escaped == "'" else "\\" + escaped)
        else:
            parts.append('\\"' if character == '"' else character)
        position += 1
    return json.loads('"' + "".join(parts) + '"')


def _query_tokens(path: str) -> List[Any]:
    """Parse a deliberately small JSON path grammar without evaluating code."""
    if not isinstance(path, str):
        raise TypeError("path must be a string")
    tokens: List[Any] = []
    position = 1 if path.startswith("$") else 0
    while position < len(path):
        if path[position] == "[":
            match = _QUERY_BRACKET.match(path, position)
            if match is None:
                raise ValueError("invalid bracket selector in JSON path")
            index, wildcard, key = match.groups()
            if index is not None:
                tokens.append(int(index))
            elif wildcard is not None:
                tokens.append(_WILDCARD)
            else:
                try:
                    tokens.append(_quoted_query_key(key))
                except ValueError as exc:
                    raise ValueError("invalid quoted key in JSON path") from exc
            position = match.end()
            continue
        if path[position] == ".":
            if position == 0:
                raise ValueError("JSON path cannot start with a dot")
            position += 1
        elif position != 0:
            raise ValueError("expected a dot or bracket in JSON path")
        if position < len(path) and path[position] == "*":
            tokens.append(_WILDCARD)
            position += 1
            continue
        match = _QUERY_KEY.match(path, position)
        if match is None:
            raise ValueError("expected an object key in JSON path")
        tokens.append(match.group())
        position = match.end()
    return tokens


def json_query(obj: Any, path: str) -> List[Any]:
    """Select values using a small, deterministic JSONPath-style syntax.

    Supports ``$.items[*].name``, ``items[-1]``, ``$['a.b']`` and object
    wildcards. ``$`` or an empty path selects the root. Always returns a list;
    missing keys, indexes and incompatible types produce no matches. Explicit
    nulls remain ``None`` in the results, and input data is never modified.

    Invalid syntax raises ValueError; a non-string path raises TypeError.
    Recursive descent, slices, filters and expressions are not supported.
    """
    matches = [obj]
    for token in _query_tokens(path):
        selected: List[Any] = []
        for value in matches:
            if token is _WILDCARD:
                if isinstance(value, dict):
                    selected.extend(value.values())
                elif isinstance(value, list):
                    selected.extend(value)
            elif isinstance(token, str) and isinstance(value, dict):
                if token in value:
                    selected.append(value[token])
            elif isinstance(token, int) and isinstance(value, list):
                if -len(value) <= token < len(value):
                    selected.append(value[token])
        matches = selected
    return matches


def _json_segments(text: str) -> List[tuple[int, int]]:
    """Find JSON object/array boundaries in text."""
    segments: List[tuple[int, int]] = []
    stack: List[str] = []
    start = -1
    in_string = False
    escaped = False

    for idx, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch in "{[":
            if not stack:
                start = idx
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            open_ch = stack.pop()
            if (open_ch == "{" and ch == "}") or (open_ch == "[" and ch == "]"):
                if not stack and start >= 0:
                    segments.append((start, idx + 1))
                    start = -1
            else:
                start = -1
                stack.clear()
    return segments


def find_first(text: str) -> Any:
    """
    Find and parse the first JSON object or array in text.

    Args:
        text: Text that may contain embedded JSON

    Returns:
        Parsed JSON object/array, or None if not found
    """
    for start, end in _json_segments(text):
        chunk = text[start:end]
        try:
            return json.loads(chunk)
        except Exception:
            continue
    return None


def find_all(text: str) -> List[Any]:
    """
    Find and parse all JSON objects and arrays in text.

    Args:
        text: Text that may contain embedded JSON

    Returns:
        List of parsed JSON objects/arrays
    """
    items: List[Any] = []
    for start, end in _json_segments(text):
        chunk = text[start:end]
        try:
            items.append(json.loads(chunk))
        except Exception:
            continue
    return items


def get(obj: Any, *path: Any) -> Any:
    """
    Safely access nested JSON properties.

    Never throws - returns None for any missing key/index.

    Args:
        obj: JSON object (dict or list)
        *path: Keys (str) or indices (int) to traverse

    Returns:
        Value at path, or None if not found

    Examples:
        >>> get({"user": {"name": "Alice"}}, "user", "name")
        'Alice'
        >>> get([{"id": 1}], 0, "id")
        1
        >>> get({}, "missing", "key")
        None
    """
    current = obj
    for part in path:
        if isinstance(part, str):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        elif isinstance(part, int):
            if isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
            else:
                return None
        else:
            return None
    return current


# Aliases for backward compatibility
find_first_json = find_first
find_all_json = find_all
json_get = get


__all__ = [
    "find_first",
    "find_all",
    "get",
    # Aliases
    "find_first_json",
    "find_all_json",
    "json_get",
    "json_query",
    "json_pointer", "json_flatten", "json_merge_patch", "json_project",
    "iter_jsonl", "jsonl_dumps", "records_to_csv", "csv_to_records",
]
