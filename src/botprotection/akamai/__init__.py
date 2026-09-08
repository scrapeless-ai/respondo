"""
Akamai Bot Manager Protection Parsing

Handles extraction of Akamai sensor data, pixel paths, and session-based (SBSD) data.
No external dependencies - uses stdlib only (re, json).
"""

import re
from typing import Any, Dict


def extract_sensor_script(html_text: str) -> str:
    """
    Extract Akamai Bot Manager sensor script URL from HTML.

    Args:
        html_text: HTML content from Akamai-protected page

    Returns:
        Script URL (e.g., https://...akam/[id]/[filename]) or empty string
    """
    if not html_text:
        return ""
    try:
        # Pattern: <script src="https://...akam/[number]/[word]...">
        match = re.search(r'<script[^>]+src=["\'](https://[^"\']*akam/\d+/\w+[^"\']*)["\']', html_text)
        if match:
            return match.group(1)
        return ""
    except Exception:
        return ""


def extract_sensor_data(html_text: str) -> Dict[str, Any]:
    """
    Extract Akamai sensor challenge data from HTML.

    Looks for sensor parameters like:
    - bazadebezolkohpepadr (numeric HTML variable)
    - Script arrays containing sensor values

    Args:
        html_text: HTML content from Akamai challenge

    Returns:
        Dict with keys: 'var', 'script_url', 'sensor_value' or empty dict
    """
    if not html_text:
        return {}

    result = {}

    try:
        # Extract numeric value from HTML variable
        var_match = re.search(r'bazadebezolkohpepadr["\']?\s*[:=]\s*["\']?(\d+)', html_text)
        if var_match:
            result['var'] = var_match.group(1)

        # Extract script URL
        script_match = re.search(r'<script[^>]+src=["\'](https://[^"\']*akam/\d+/\w+[^"\']*)["\']', html_text)
        if script_match:
            result['script_url'] = script_match.group(1)

        # Look for array variable containing sensor data
        # Pattern: var xxx = ["value1", "value2", ...]; or var xxx = 'value'
        array_match = re.search(r'var\s+\w+\s*=\s*\[([^\]]+)\]', html_text)
        if array_match:
            values = array_match.group(1)
            # Extract all quoted strings
            quoted = re.findall(r'["\']([^"\']+)["\']', values)
            if quoted:
                result['sensor_array'] = quoted

        return result
    except Exception:
        return {}


def extract_pixel_path(html_text: str, script_content: str = "") -> str:
    """
    Extract Akamai pixel challenge posting path.

    Converts script filename to pixel endpoint:
    - Script: https://...akam/123/abcd -> Pixel: pixel_abcd

    Args:
        html_text: HTML page content
        script_content: Downloaded script content

    Returns:
        Pixel path (e.g., "pixel_abcd") or empty string
    """
    if not html_text:
        return ""

    try:
        # Extract script filename from URL
        script_match = re.search(r'akam/\d+/(\w+)', html_text)
        if script_match:
            filename = script_match.group(1)
            return f"pixel_{filename}"
        return ""
    except Exception:
        return ""


def parse_sbsd_data(html_text: str) -> Dict[str, str]:
    """
    Parse Akamai SBSD (Session-Based) sensor data from HTML.

    Extracts values for:
    - Session index
    - User agent detection
    - UUID/session identifiers

    Args:
        html_text: HTML content

    Returns:
        Dict with 'index', 'uuid', 'session_id' or empty dict
    """
    if not html_text:
        return {}

    result = {}

    try:
        # Look for session index in script
        index_match = re.search(r'index["\']?\s*[:=]\s*["\']?(\d+)', html_text)
        if index_match:
            result['index'] = index_match.group(1)

        # Extract UUID patterns (standard UUID format)
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', html_text, re.I)
        if uuid_match:
            result['uuid'] = uuid_match.group(1)

        # Look for session identifiers
        session_match = re.search(r'["\']?(?:session|_sid)["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if session_match:
            result['session_id'] = session_match.group(1)

        return result
    except Exception:
        return {}


__all__ = [
    "extract_sensor_script",
    "extract_sensor_data",
    "extract_pixel_path",
    "parse_sbsd_data",
]
