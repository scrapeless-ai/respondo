"""
Google reCAPTCHA Detection and Extraction

Handles extraction of reCAPTCHA site keys and detection of reCAPTCHA presence.
No external dependencies - uses stdlib only (re).
"""

import re
from typing import List


# reCAPTCHA patterns (site keys are typically 40 chars but can vary)
_SITEKEY_PATTERNS = [
    # data-sitekey attribute (keys start with 6L and are 40+ chars)
    re.compile(r'data-sitekey=["\']([a-zA-Z0-9_-]{20,50})["\']'),
    # Script src with render parameter
    re.compile(r'google\.com/recaptcha/(?:api|enterprise)\.js\?[^"\']*render=([a-zA-Z0-9_-]{20,50})'),
    # grecaptcha.execute('sitekey', ...)
    re.compile(r'grecaptcha\.execute\s*\(\s*["\']([a-zA-Z0-9_-]{10,50})["\']'),
    # grecaptcha.render with sitekey
    re.compile(r'grecaptcha\.render\s*\([^)]*sitekey\s*:\s*["\']([a-zA-Z0-9_-]{20,50})["\']'),
]

_DETECT_PATTERNS = [
    re.compile(r'class=["\'][^"\']*g-recaptcha', re.IGNORECASE),
    re.compile(r'google\.com/recaptcha/', re.IGNORECASE),
    re.compile(r'grecaptcha\.', re.IGNORECASE),
    re.compile(r'www\.gstatic\.com/recaptcha/', re.IGNORECASE),
]


def extract_sitekey(html: str) -> List[str]:
    """
    Extract reCAPTCHA site keys from HTML.

    Args:
        html: HTML content to search

    Returns:
        List of unique site keys found
    """
    if not html:
        return []
    results = []
    seen = set()
    for pattern in _SITEKEY_PATTERNS:
        for match in pattern.findall(html):
            if match not in seen:
                seen.add(match)
                results.append(match)
    return results


def contains(html: str) -> bool:
    """
    Check if HTML contains reCAPTCHA.

    Args:
        html: HTML content to check

    Returns:
        True if reCAPTCHA is detected
    """
    if not html:
        return False
    return any(p.search(html) for p in _DETECT_PATTERNS)


__all__ = [
    "extract_sitekey",
    "contains",
]
