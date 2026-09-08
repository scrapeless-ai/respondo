"""
DataDome Protection Parsing

Handles extraction of DataDome CAPTCHA challenges, URLs, and challenge parameters.
No external dependencies - uses stdlib only (re, json).
"""

import json
import re
from typing import Any, Dict


def extract_object(html_text: str) -> Dict[str, Any]:
    """
    Extract DataDome JavaScript object from HTML.

    Searches for: var dd = {cid, hsh, t, s, e, ...}
    Converts to valid JSON for parsing.

    Args:
        html_text: HTML content from DataDome challenge page

    Returns:
        Parsed JSON object or empty dict
    """
    if not html_text:
        return {}

    try:
        # Find the DataDome object using regex to handle variable spacing
        match = re.search(r'(?:var\s+)?dd\s*=\s*\{', html_text)
        if not match:
            return {}

        # Find where the opening brace starts
        start_idx = match.end() - 1  # Position at the opening brace

        # Skip whitespace after var dd=
        while start_idx < len(html_text) and html_text[start_idx] in ' \t\n':
            start_idx += 1

        # Find the closing brace
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(html_text)):
            if html_text[i] == '{':
                brace_count += 1
            elif html_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            return {}

        # Extract the object string
        obj_str = html_text[start_idx:end_idx].strip()

        # Remove trailing semicolons
        obj_str = obj_str.rstrip(';').strip()

        # Convert single quotes to double quotes for JSON compliance
        obj_str = obj_str.replace("'", '"')

        # Parse as JSON
        return json.loads(obj_str)
    except Exception:
        return {}


def build_slider_url(dd_object: Dict[str, Any], cookie_value: str, referrer: str) -> str:
    """
    Build DataDome slider puzzle challenge URL from parsed object.

    URL format: https://geo.captcha-delivery.com/captcha/?cid=...&hsh=...&t=...

    Args:
        dd_object: Parsed DataDome object from extract_object()
        cookie_value: Current datadome cookie value
        referrer: Request referrer URL

    Returns:
        Full challenge URL or empty string
    """
    if not dd_object:
        return ""

    try:
        # Check for proxy block indicator
        if dd_object.get('t') == 'bv':
            return ""  # Proxy blocked

        # Extract required parameters
        params = {
            'cid': dd_object.get('cid', ''),
            'hsh': dd_object.get('hsh', ''),
            't': dd_object.get('t', ''),
            's': dd_object.get('s', ''),
            'e': str(dd_object.get('e', ''))
        }

        # Remove empty values
        params = {k: v for k, v in params.items() if v}

        if not params:
            return ""

        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        query_string = '&'.join(query_parts)

        return f"https://geo.captcha-delivery.com/captcha/?{query_string}"
    except Exception:
        return ""


def build_interstitial_url(dd_object: Dict[str, Any], cookie_value: str, referrer: str) -> str:
    """
    Build DataDome interstitial challenge URL from parsed object.

    Similar to slider but includes 'b' field and different endpoint.

    Args:
        dd_object: Parsed DataDome object from extract_object()
        cookie_value: Current datadome cookie value
        referrer: Request referrer URL

    Returns:
        Full challenge URL or empty string
    """
    if not dd_object:
        return ""

    try:
        params = {
            'cid': dd_object.get('cid', ''),
            'hsh': dd_object.get('hsh', ''),
            't': dd_object.get('t', ''),
            's': dd_object.get('s', ''),
            'b': dd_object.get('b', ''),
            'e': str(dd_object.get('e', ''))
        }

        # Remove empty values
        params = {k: v for k, v in params.items() if v}

        if not params:
            return ""

        query_parts = [f"{k}={v}" for k, v in params.items()]
        query_string = '&'.join(query_parts)

        return f"https://geo.captcha-delivery.com/interstitial/?{query_string}"
    except Exception:
        return ""


def extract_captcha_images(html_text: str) -> Dict[str, str]:
    """
    Extract DataDome CAPTCHA puzzle and piece images from HTML.

    Returns base64-encoded image data.

    Args:
        html_text: HTML from CAPTCHA page

    Returns:
        Dict with 'puzzle' and 'piece' keys (base64 strings) or empty dict
    """
    if not html_text:
        return {}

    result = {}

    try:
        # Look for data URLs in image tags or canvas elements
        puzzle_match = re.search(r'<img[^>]+src=["\'](data:image/[^"\']+)["\']', html_text)
        if puzzle_match:
            result['puzzle'] = puzzle_match.group(1)

        # Look for piece image
        piece_match = re.search(r'id=["\']piece["\'][^>]*src=["\'](data:image/[^"\']+)["\']', html_text)
        if piece_match:
            result['piece'] = piece_match.group(1)

        return result
    except Exception:
        return {}


__all__ = [
    "extract_object",
    "build_slider_url",
    "build_interstitial_url",
    "extract_captcha_images",
]
