"""
Bot Protection Detection and Unified API

Detects which bot protection system is in use and provides unified access to all parsing functions.
"""

import re
from typing import Any, Dict, List

# Import all protection system parsers
from . import akamai
from . import datadome
from . import incapsula
from . import kasada
from . import recaptcha
from . import turnstile
from . import hcaptcha


def detect_system(html_text: str) -> str:
    """
    Detect which bot protection system is protecting the page.

    Args:
        html_text: HTML content from page

    Returns:
        'akamai', 'datadome', 'incapsula', 'kasada', 'recaptcha', 'turnstile', 'hcaptcha', or 'unknown'
    """
    if not html_text:
        return "unknown"

    # Check for DataDome indicators FIRST (can sometimes appear with others)
    if re.search(r'var\s+dd\s*=|datadome|captcha-delivery\.com', html_text, re.I):
        return "datadome"

    # Check for Akamai indicators
    if re.search(r'akam|_abck|bazadebezolkohpepadr', html_text, re.I):
        return "akamai"

    # Check for Incapsula indicators
    if re.search(r'Pardon Our Interruption|_Incapsula_Resource|imperva', html_text, re.I):
        return "incapsula"

    # Check for Kasada indicators
    if re.search(r'x-kpsdk|kpsdk|kasada', html_text, re.I):
        return "kasada"

    # Check for reCAPTCHA
    if recaptcha.contains(html_text):
        return "recaptcha"

    # Check for Turnstile
    if turnstile.contains(html_text):
        return "turnstile"

    # Check for hCaptcha
    if hcaptcha.contains(html_text):
        return "hcaptcha"

    return "unknown"


def detect_all_systems(html_text: str) -> List[str]:
    """
    Detect ALL bot protection systems present on the page.

    Unlike detect_system() which returns the first match, this returns all systems found.
    A page can have multiple protections (e.g., Akamai + reCAPTCHA).

    Args:
        html_text: HTML content from page

    Returns:
        List of detected systems (can be empty)
    """
    if not html_text:
        return []

    systems = []

    # Check each system
    if re.search(r'var\s+dd\s*=|datadome|captcha-delivery\.com', html_text, re.I):
        systems.append("datadome")

    if re.search(r'akam|_abck|bazadebezolkohpepadr', html_text, re.I):
        systems.append("akamai")

    if re.search(r'Pardon Our Interruption|_Incapsula_Resource|imperva', html_text, re.I):
        systems.append("incapsula")

    if re.search(r'x-kpsdk|kpsdk|kasada', html_text, re.I):
        systems.append("kasada")

    if recaptcha.contains(html_text):
        systems.append("recaptcha")

    if turnstile.contains(html_text):
        systems.append("turnstile")

    if hcaptcha.contains(html_text):
        systems.append("hcaptcha")

    return systems


def extract_all(html_text: str, url: str = "", script_content: str = "") -> Dict[str, Any]:
    """
    Extract all available protection data based on detected systems.

    Provides a unified interface for extracting challenge data from any system.
    Now extracts data for ALL detected systems, not just the first one.

    Args:
        html_text: HTML page content
        url: Current request URL
        script_content: Optional downloaded script content

    Returns:
        Dict with 'systems' key (list) and protection-specific data for each system
    """
    if not html_text:
        return {}

    systems = detect_all_systems(html_text)
    result = {"systems": systems, "system": systems[0] if systems else "unknown"}

    try:
        # Akamai
        if "akamai" in systems:
            result['akamai'] = {
                'sensor_script': akamai.extract_sensor_script(html_text),
                'sensor_data': akamai.extract_sensor_data(html_text),
                'sbsd_data': akamai.parse_sbsd_data(html_text),
            }

        # DataDome
        if "datadome" in systems:
            dd_obj = datadome.extract_object(html_text)
            result['datadome'] = {
                'dd_object': dd_obj,
                'slider_url': datadome.build_slider_url(dd_obj, "", url),
                'interstitial_url': datadome.build_interstitial_url(dd_obj, "", url),
                'captcha_images': datadome.extract_captcha_images(html_text),
            }

        # Incapsula
        if "incapsula" in systems:
            result['incapsula'] = {
                'is_challenge': incapsula.is_challenge_page(html_text),
                'paths': incapsula.extract_script_paths(html_text, url),
                'utmvc_path': incapsula.extract_utmvc_script_path(script_content),
                'nonce': incapsula.extract_nonce(html_text),
            }

        # Kasada
        if "kasada" in systems:
            result['kasada'] = {
                'endpoints': kasada.extract_endpoints(html_text),
                'challenge_data': kasada.extract_challenge_data(html_text),
                'fingerprint': kasada.extract_fingerprint_context(script_content),
            }

        # reCAPTCHA
        if "recaptcha" in systems:
            result['recaptcha'] = {
                'sitekeys': recaptcha.extract_sitekey(html_text),
            }

        # Turnstile
        if "turnstile" in systems:
            result['turnstile'] = {
                'sitekeys': turnstile.extract_sitekey(html_text),
            }

        # hCaptcha
        if "hcaptcha" in systems:
            result['hcaptcha'] = {
                'sitekeys': hcaptcha.extract_sitekey(html_text),
            }

    except Exception:
        pass

    return result


__all__ = [
    "detect_system",
    "detect_all_systems",
    "extract_all",
]
