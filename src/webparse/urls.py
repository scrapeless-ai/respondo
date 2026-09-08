"""Conservative HTTP(S) URL transformations; never fetch URLs."""

import math
import ipaddress
import re
from collections.abc import Mapping
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


def _http_url(url: str, base: Optional[str] = None):
    if not isinstance(url, str) or (base is not None and not isinstance(base, str)):
        raise TypeError("URL and base must be strings")
    for value in (url, base):
        if value is not None and (re.search(r"[\x00-\x20\x7f]", value) or "\\" in value):
            raise ValueError("URL must not contain whitespace, controls or backslashes")
    try:
        parts = urlsplit(urljoin(base, url) if base else url)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ValueError
        if parts.username is not None or parts.password is not None:
            raise ValueError
        port = parts.port
        host = parts.hostname.encode("idna").decode("ascii").lower()
        if ":" in host:
            ipaddress.IPv6Address(host)
            if not re.fullmatch(r"\[[^\]]+\](?::[0-9]*)?", parts.netloc):
                raise ValueError
            host = "[" + host + "]"
        elif "[" in parts.netloc or not re.fullmatch(r"[a-z0-9.-]+", host):
            raise ValueError
        if port is not None and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
            host += ":" + str(port)
        return parts._replace(scheme=parts.scheme.lower(), netloc=host, path=parts.path or "/")
    except (ValueError, UnicodeError):
        raise ValueError("expected an absolute HTTP(S) URL without credentials and with a valid host/port") from None


def _query_pairs(query: str) -> list:
    try:
        return parse_qsl(query, keep_blank_values=True, errors="strict")
    except UnicodeError:
        raise ValueError("query parameters must use valid UTF-8 percent encoding for transformations") from None


def normalize_url(url: str, *, base: Optional[str] = None, drop_fragment: bool = False,
                  remove_tracking: bool = False, sort_query: bool = False) -> str:
    """Lowercase scheme/IDNA host, remove default ports, and supply an empty-path /.

    Preserve path case, encoded separators and raw query by default. Explicit
    options remove fragments, drop utm_* / fbclid / gclid / msclkid parameters,
    or sort query pairs by key then value. Query transforms re-encode query pairs
    and reject non-UTF-8 percent-encoded values instead of silently replacing them.
    Relative inputs require base. Credentials, controls, whitespace, backslashes,
    unsupported schemes and invalid ports raise ValueError without echoing input.
    Hostnames use IDNA; percent-encoded hosts and IPvFuture literals are unsupported.
    This is not an SSRF guard or an assurance that a URL is safe to fetch.
    """
    parts = _http_url(url, base)
    query = parts.query
    if remove_tracking or sort_query:
        pairs = _query_pairs(query)
        if remove_tracking:
            pairs = [(key, value) for key, value in pairs
                     if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid", "msclkid"}]
        if sort_query:
            pairs.sort()
        query = urlencode(pairs)
    return urlunsplit(parts._replace(query=query, fragment="" if drop_fragment else parts.fragment))


def _query_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if not isinstance(value, (str, int, float)):
        raise TypeError("query values must be strings, finite numbers or booleans")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("query numbers must be finite")
    return str(value)


def update_url_query(url: str, updates: Mapping, *, base: Optional[str] = None) -> str:
    """Replace all occurrences of selected query keys; append replacements in order.

    None or [] removes a key; a list/tuple adds repeated keys. Unrelated pairs
    retain order, duplicates and blank values; fragments are retained. Query
    percent-encoding is regenerated with urlencode (spaces become +). Inputs
    use the same HTTP(S) validation and conservative normalization as normalize_url.
    """
    parts = _http_url(url, base)
    if not isinstance(updates, Mapping) or any(not isinstance(key, str) for key in updates):
        raise TypeError("query updates must map string keys to values")
    pairs = [(key, value) for key, value in _query_pairs(parts.query) if key not in updates]
    for key, value in updates.items():
        if value is None:
            continue
        values = value if isinstance(value, (list, tuple)) else [value]
        pairs.extend((key, _query_value(item)) for item in values)
    return urlunsplit(parts._replace(query=urlencode(pairs)))


__all__ = ["normalize_url", "update_url_query"]
