"""
Kasada Protection Parsing

Handles extraction of Kasada endpoints, challenge data, fingerprint context, and POW responses.
No external dependencies - uses stdlib only (re, json).
"""

import json
import re
from typing import Any, Dict


def extract_endpoints(html_text: str) -> Dict[str, str]:
    """
    Extract Kasada protection script and API endpoints from HTML.

    Looks for:
    - c.js script path
    - IPS (intelligent proof-of-work) endpoint

    Args:
        html_text: HTML from Kasada-protected page

    Returns:
        Dict with 'script_url' and 'ips_link' or empty dict
    """
    if not html_text:
        return {}

    result = {}

    try:
        # Look for c.js script
        script_match = re.search(r'<script[^>]+src=["\'](https://[^"\']*c\.js[^"\']*)["\']', html_text)
        if script_match:
            result['script_url'] = script_match.group(1)

        # Look for IPS endpoint in JSON or as URL
        ips_match = re.search(r'["\']?(?:ips_link|ipsLink)["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if ips_match:
            result['ips_link'] = ips_match.group(1)

        return result
    except Exception:
        return {}


def extract_challenge_data(html_text: str) -> Dict[str, Any]:
    """
    Extract Kasada proof-of-work challenge parameters from HTML.

    Extracts challenge parameters that need to be solved:
    - st (proof-of-work state token)
    - ct (challenge token)
    - fc (optional fingerprint cookie)

    Args:
        html_text: HTML from 429 block page

    Returns:
        Dict with 'st', 'ct', 'fc' or empty dict
    """
    if not html_text:
        return {}

    result = {}

    try:
        # Extract x-kpsdk-st value (state token)
        st_match = re.search(r'["\']?x-kpsdk-st["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if st_match:
            result['st'] = st_match.group(1)

        # Extract x-kpsdk-ct value (challenge token)
        ct_match = re.search(r'["\']?x-kpsdk-ct["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if ct_match:
            result['ct'] = ct_match.group(1)

        # Extract x-kpsdk-fc value (fingerprint cookie) - optional
        fc_match = re.search(r'["\']?x-kpsdk-fc["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_text)
        if fc_match:
            result['fc'] = fc_match.group(1)

        return result
    except Exception:
        return {}


def extract_fingerprint_context(script_content: str) -> Dict[str, Any]:
    """
    Extract fingerprinting context from Kasada c.js script.

    Looks for:
    - Device identifiers
    - Browser characteristics
    - Canvas/WebGL data

    Args:
        script_content: Content of c.js script

    Returns:
        Dict with fingerprint data or empty dict
    """
    if not script_content:
        return {}

    result = {}

    try:
        # Look for common fingerprint keys in the script
        # Pattern: "key":"value" or 'key':'value'
        pairs = re.findall(r'["\']([a-z_]+)["\']?\s*:\s*["\']([^"\']+)["\']', script_content)

        for key, value in pairs:
            # Filter for fingerprint-related keys
            if any(fp_key in key.lower() for fp_key in ['fingerprint', 'canvas', 'webgl', 'device', 'browser']):
                result[key] = value

        return result
    except Exception:
        return {}


def parse_pow_response(response_text: str) -> Dict[str, str]:
    """
    Parse Kasada proof-of-work response to extract tokens.

    Extracts:
    - x-kpsdk-st (new state token)
    - x-kpsdk-cr (challenge response)

    Args:
        response_text: Response body from POW submission

    Returns:
        Dict with token values or empty dict
    """
    if not response_text:
        return {}

    result = {}

    try:
        # Try to parse as JSON first
        try:
            data = json.loads(response_text)
            if 'st' in data:
                result['st'] = data['st']
            if 'cr' in data:
                result['cr'] = data['cr']
            return result
        except json.JSONDecodeError:
            pass

        # Fall back to regex extraction
        st_match = re.search(r'["\']?st["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
        if st_match:
            result['st'] = st_match.group(1)

        cr_match = re.search(r'["\']?cr["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
        if cr_match:
            result['cr'] = cr_match.group(1)

        return result
    except Exception:
        return {}


__all__ = [
    "extract_endpoints",
    "extract_challenge_data",
    "extract_fingerprint_context",
    "parse_pow_response",
]
