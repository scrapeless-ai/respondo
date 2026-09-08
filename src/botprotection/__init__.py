"""
Bot Protection System Parsing Module

This module provides parsing methods for major bot protection systems:
- Akamai Bot Manager
- DataDome
- Incapsula/Imperva
- Kasada
- reCAPTCHA (Google)
- Turnstile (Cloudflare)
- hCaptcha

Organized into submodules by protection system, each with zero external dependencies
(uses stdlib only: re, json, html, urllib, base64).

Returns empty values on failure (consistent with Respondo philosophy):
- str functions return "" (empty string)
- list functions return [] (empty list)
- dict functions return {} (empty dict)
- bool functions return False
"""

from typing import Dict, List

# Akamai Bot Manager
from .akamai import (
    extract_sensor_script as extract_akamai_sensor_script,
    extract_sensor_data as extract_akamai_sensor_data,
    extract_pixel_path as extract_akamai_pixel_path,
    parse_sbsd_data as parse_akamai_sbsd_data,
)

# DataDome
from .datadome import (
    extract_object as extract_datadome_object,
    build_slider_url as build_datadome_slider_url,
    build_interstitial_url as build_datadome_interstitial_url,
    extract_captcha_images as extract_datadome_captcha_images,
)

# Incapsula/Imperva
from .incapsula import (
    is_challenge_page as extract_incapsula_challenge_marker,
    extract_script_paths as extract_incapsula_script_paths,
    extract_utmvc_script_path as extract_incapsula_utmvc_script_path,
    generate_submit_path as generate_incapsula_submit_path,
    extract_nonce as extract_incapsula_nonce,
)

# Kasada
from .kasada import (
    extract_endpoints as extract_kasada_endpoints,
    extract_challenge_data as extract_kasada_challenge_data,
    extract_fingerprint_context as extract_kasada_fingerprint_context,
    parse_pow_response as parse_kasada_pow_response,
)

# reCAPTCHA (Google)
from .recaptcha import (
    extract_sitekey as extract_recaptcha_sitekey,
    contains as contains_recaptcha,
)

# Turnstile (Cloudflare)
from .turnstile import (
    extract_sitekey as extract_turnstile_sitekey,
    contains as contains_turnstile,
)

# hCaptcha
from .hcaptcha import (
    extract_sitekey as extract_hcaptcha_sitekey,
    contains as contains_hcaptcha,
)

# Detection and Unified API
from .detect import (
    detect_system as detect_protection_system,
    detect_all_systems as detect_all_protection_systems,
    extract_all as extract_all_protection_data,
)


def extract_captcha_params(html: str) -> Dict[str, List[str]]:
    """
    Extract all captcha parameters from HTML.

    Args:
        html: HTML content to search

    Returns:
        Dict with 'recaptcha', 'turnstile', 'hcaptcha' keys containing sitekey lists
    """
    return {
        "recaptcha": extract_recaptcha_sitekey(html),
        "turnstile": extract_turnstile_sitekey(html),
        "hcaptcha": extract_hcaptcha_sitekey(html),
    }


__all__ = [
    # Akamai
    "extract_akamai_sensor_script",
    "extract_akamai_sensor_data",
    "extract_akamai_pixel_path",
    "parse_akamai_sbsd_data",
    # DataDome
    "extract_datadome_object",
    "build_datadome_slider_url",
    "build_datadome_interstitial_url",
    "extract_datadome_captcha_images",
    # Incapsula
    "extract_incapsula_challenge_marker",
    "extract_incapsula_script_paths",
    "extract_incapsula_utmvc_script_path",
    "generate_incapsula_submit_path",
    "extract_incapsula_nonce",
    # Kasada
    "extract_kasada_endpoints",
    "extract_kasada_challenge_data",
    "extract_kasada_fingerprint_context",
    "parse_kasada_pow_response",
    # reCAPTCHA
    "extract_recaptcha_sitekey",
    "contains_recaptcha",
    # Turnstile
    "extract_turnstile_sitekey",
    "contains_turnstile",
    # hCaptcha
    "extract_hcaptcha_sitekey",
    "contains_hcaptcha",
    # Combined captcha
    "extract_captcha_params",
    # Detection
    "detect_protection_system",
    "detect_all_protection_systems",
    "extract_all_protection_data",
]
