"""
Cloudflare Turnstile Detection and Extraction

Handles extraction of Turnstile site keys and detection of Turnstile presence.
No external dependencies - uses stdlib only (re).
"""

import re
from typing import List


# Turnstile (Cloudflare) patterns
_SITEKEY_PATTERNS = [
    # data-sitekey on cf-turnstile
    re.compile(r'class=["\'][^"\']*cf-turnstile[^"\']*["\'][^>]*data-sitekey=["\']([a-zA-Z0-9_-]+)["\']'),
    re.compile(r'data-sitekey=["\']([0x][a-zA-Z0-9_-]+)["\']'),
    # turnstile.render with sitekey
    re.compile(r'turnstile\.render\s*\([^)]*sitekey\s*:\s*["\']([0x][a-zA-Z0-9_-]+)["\']'),
    # Script with render parameter
    re.compile(r'challenges\.cloudflare\.com/turnstile/[^"\']*\?[^"\']*render=([0x][a-zA-Z0-9_-]+)'),
]

_DETECT_PATTERNS = [
    re.compile(r'class=["\'][^"\']*cf-turnstile', re.IGNORECASE),
    re.compile(r'challenges\.cloudflare\.com/turnstile/', re.IGNORECASE),
    re.compile(r'turnstile\.render', re.IGNORECASE),
]


def extract_sitekey(html: str) -> List[str]:
    """
    Extract Cloudflare Turnstile site keys from HTML.

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
    Check if HTML contains Cloudflare Turnstile.

    Args:
        html: HTML content to check

    Returns:
        True if Turnstile is detected
    """
    if not html:
        return False
    return any(p.search(html) for p in _DETECT_PATTERNS)


__all__ = [
    "extract_sitekey",
    "contains",
]
