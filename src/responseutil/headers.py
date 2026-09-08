"""Explicit parsing of Retry-After and Link metadata; never wait or follow links."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import re
from typing import Optional
from urllib.parse import urljoin


_TOKEN = r"[!#$%&'*+.^_`|~0-9A-Za-z-]+"
_PARAM = re.compile(r"(" + _TOKEN + r')(?:\s*=\s*(?:"((?:[^"\\]|\\.)*)"|(' + _TOKEN + r")))?")
_DAY = r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_TIME = r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
_HTTP_DATE = re.compile(
    _DAY + r", [0-9]{2} " + _MONTH + r" [0-9]{4} " + _TIME + r" GMT|"
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), [0-9]{2}-" + _MONTH + r"-[0-9]{2} " + _TIME + r" GMT|"
    + _DAY + r" " + _MONTH + r" (?: [0-9]|[0-9]{2}) " + _TIME + r" [0-9]{4}"
)


def retry_after(value: str, now: Optional[datetime] = None) -> Optional[float]:
    if now is not None and (now.tzinfo is None or now.utcoffset() is None):
        raise ValueError("now must be a timezone-aware datetime")
    if re.search(r"[\x00-\x08\x0a-\x1f\x7f]", value):
        return None
    value = value.strip(" \t")
    if not value:
        return None
    try:
        if re.fullmatch(r"[0-9]+", value):
            seconds = float(value)
            return seconds if math.isfinite(seconds) else None
        if not _HTTP_DATE.fullmatch(value):
            return None
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return max(0.0, (date - (now or datetime.now(timezone.utc))).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return None


def _split(value: str, separator: str) -> list:
    parts = []
    start = 0
    quoted = escaped = angle = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
        elif quoted and character == "\\":
            escaped = True
        elif character == '"' and not angle:
            quoted = not quoted
        elif not quoted:
            if character == "<":
                if angle:
                    raise ValueError("invalid Link header")
                angle = True
            elif character == ">":
                if not angle:
                    raise ValueError("invalid Link header")
                angle = False
            elif character == separator and not angle:
                parts.append(value[start:index].strip())
                start = index + 1
    if quoted or angle or escaped:
        raise ValueError("invalid Link header")
    parts.append(value[start:].strip())
    return parts


def parse_links(values: list, base: Optional[str] = None) -> list:
    links = []
    for value in values:
        if re.search(r"[\x00-\x08\x0a-\x1f\x7f]", value):
            raise ValueError("invalid control character in Link header")
        for member in _split(value, ","):
            if not member:
                continue  # Empty list members are allowed by HTTP list parsing.
            pieces = _split(member, ";")
            target = re.fullmatch(r"<([^<>\s]*)>", pieces[0])
            if not target:
                raise ValueError("invalid Link target")
            params = {}
            for piece in pieces[1:]:
                param = _PARAM.fullmatch(piece)
                if not param:
                    raise ValueError("invalid Link parameter")
                name, quoted, token = param.groups()
                decoded = re.sub(r"\\(.)", r"\1", quoted) if quoted is not None else token or ""
                params.setdefault(name.lower(), decoded)
            target_url = target.group(1)
            try:
                resolved = urljoin(base, target_url) if base else target_url
            except ValueError:
                raise ValueError("invalid Link target or base") from None
            links.append({"url": resolved, "rel": params.get("rel", "").split(), "params": params})
    return links
