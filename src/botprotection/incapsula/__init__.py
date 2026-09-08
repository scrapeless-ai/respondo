"""
Incapsula/Imperva Protection Parsing

Handles extraction of Incapsula challenge detection, script paths, UTMVC tokens, and nonces.
No external dependencies - uses stdlib only (re).
"""

import re
from typing import Dict


def is_challenge_page(html_text: str) -> bool:
    """
    Check if HTML contains Incapsula challenge page.

    Looks for: "Pardon Our Interruption" text

    Args:
        html_text: HTML content

    Returns:
        True if Incapsula challenge detected, False otherwise
    """
    if not html_text:
        return False
    return "Pardon Our Interruption" in html_text


def extract_script_paths(html_text: str, url: str) -> Dict[str, str]:
    """
    Extract Incapsula/Imperva challenge script paths from HTML.

    Extracts both full path and sensor path, appending hostname to sensor path.

    Args:
        html_text: HTML from Incapsula challenge
        url: Request URL (for hostname extraction)

    Returns:
        Dict with 'sensor_path' and 'script_path' or empty dict
    """
    if not html_text or not url:
        return {}

    result = {}

    try:
        # Extract hostname from URL
        hostname_match = re.search(r'https?://([^/]+)', url)
        hostname = hostname_match.group(1) if hostname_match else ""

        # Pattern: src="((/[^/]+/\d+)(?:\?.*)?)"
        # Captures both full path and shortened sensor path
        path_match = re.search(r'src=["\']((/[^/]+/\d+)(?:\?[^"\']*)?)["\']', html_text)

        if path_match:
            full_path = path_match.group(1)
            sensor_path = path_match.group(2)

            result['script_path'] = full_path

            # Append hostname to sensor path as query parameter
            if hostname:
                result['sensor_path'] = f"{sensor_path}?d={hostname}"
            else:
                result['sensor_path'] = sensor_path

        return result
    except Exception:
        return {}


def extract_utmvc_script_path(script_content: str) -> str:
    """
    Extract Incapsula UTMVC resource submission path from script.

    Looks for: /_Incapsula_Resource?...

    Args:
        script_content: JavaScript content from script tag

    Returns:
        Resource path (e.g., /_Incapsula_Resource?SWKMTFSR=...) or empty string
    """
    if not script_content:
        return ""

    try:
        # Pattern: /_Incapsula_Resource?[attributes]
        match = re.search(r'(/_Incapsula_Resource\?[^"\'\s<>]+)', script_content)
        if match:
            return match.group(1)
        return ""
    except Exception:
        return ""


def generate_submit_path(base_path: str) -> str:
    """
    Generate Incapsula challenge submission path with random parameter.

    Appends random float to: /_Incapsula_Resource?SWKMTFSR=1&e={random}

    Args:
        base_path: Base resource path (e.g., /_Incapsula_Resource)

    Returns:
        Full submission path or empty string
    """
    if not base_path:
        return ""

    try:
        import random
        random_value = random.random()
        return f"{base_path}?SWKMTFSR=1&e={random_value}"
    except Exception:
        return ""


def extract_nonce(html_text: str) -> str:
    """
    Extract Incapsula nonce/token from HTML for challenge submission.

    Args:
        html_text: HTML from challenge page

    Returns:
        Nonce value or empty string
    """
    if not html_text:
        return ""

    try:
        # Look for nonce in various formats
        nonce_match = re.search(r'["\']?(?:nonce|_Incapsula_Nonce)["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if nonce_match:
            return nonce_match.group(1)

        # Alternative: look in hidden input
        input_match = re.search(r'<input[^>]+name=["\']_Incapsula_Nonce["\'][^>]*value=["\']([^"\']+)["\']', html_text)
        if input_match:
            return input_match.group(1)

        return ""
    except Exception:
        return ""


__all__ = [
    "is_challenge_page",
    "extract_script_paths",
    "extract_utmvc_script_path",
    "generate_submit_path",
    "extract_nonce",
]
