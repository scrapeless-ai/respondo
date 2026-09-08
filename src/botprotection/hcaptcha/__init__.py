"""
hCaptcha Detection and Extraction

Handles extraction of hCaptcha site keys and detection of hCaptcha presence.
No external dependencies - uses stdlib only (re).
"""

import re
from typing import List


# hCaptcha patterns
_SITEKEY_PATTERNS = [
    # data-sitekey on h-captcha
    re.compile(r'class=["\'][^"\']*h-captcha[^"\']*["\'][^>]*data-sitekey=["\']([a-f0-9-]{36})["\']'),
    re.compile(r'data-sitekey=["\']([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})["\']'),
    # Script with sitekey parameter
    re.compile(r'hcaptcha\.com/[^"\']*\?[^"\']*sitekey=([a-f0-9-]{36})'),
    # hcaptcha.render with sitekey
    re.compile(r'hcaptcha\.render\s*\([^)]*sitekey\s*:\s*["\']([a-f0-9-]{36})["\']'),
]

_DETECT_PATTERNS = [
    re.compile(r'class=["\'][^"\']*h-captcha', re.IGNORECASE),
    re.compile(r'hcaptcha\.com/', re.IGNORECASE),
    re.compile(r'hcaptcha\.render', re.IGNORECASE),
]


def extract_sitekey(html: str) -> List[str]:
    """
    Extract hCaptcha site keys from HTML.

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
    Check if HTML contains hCaptcha.

    Args:
        html: HTML content to check

    Returns:
        True if hCaptcha is detected
    """
    if not html:
        return False
    return any(p.search(html) for p in _DETECT_PATTERNS)


__all__ = [
    "extract_sitekey",
    "contains",
]
