#!/usr/bin/env python3
"""
Bot Protection Parsing Tests

Tests for Akamai, DataDome, Incapsula, and Kasada protection system parsing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from botprotection import (
    # Akamai
    extract_akamai_sensor_script,
    extract_akamai_sensor_data,
    extract_akamai_pixel_path,
    parse_akamai_sbsd_data,
    # DataDome
    extract_datadome_object,
    build_datadome_slider_url,
    build_datadome_interstitial_url,
    extract_datadome_captcha_images,
    # Incapsula
    extract_incapsula_challenge_marker,
    extract_incapsula_script_paths,
    extract_incapsula_utmvc_script_path,
    generate_incapsula_submit_path,
    extract_incapsula_nonce,
    # Kasada
    extract_kasada_endpoints,
    extract_kasada_challenge_data,
    extract_kasada_fingerprint_context,
    parse_kasada_pow_response,
    # Detection
    detect_protection_system,
    extract_all_protection_data,
)

passed = 0
failed = 0


def test(name: str, result, expected):
    global passed, failed
    if result == expected:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        print(f"         Expected: {expected}")
        print(f"         Got:      {result}")
        failed += 1


def test_true(name: str, result):
    test(name, result, True)


def test_false(name: str, result):
    test(name, result, False)


def test_not_empty(name: str, result):
    global passed, failed
    if result and len(result) > 0:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name} - Expected non-empty result, got: {result}")
        failed += 1


def section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def main():
    global passed, failed

    print("\n" + "="*60)
    print("    BOT PROTECTION PARSING - Test Suite")
    print("="*60)

    # =========================================================================
    section("AKAMAI BOT MANAGER PARSING")
    # =========================================================================

    # Test Akamai script extraction
    akamai_html = '''
    <html>
    <head>
        <script src="https://cdn.bootcss.com/akam/12345/abcde_xyz.js"></script>
    </head>
    </html>
    '''
    test("extract_akamai_sensor_script - valid",
         extract_akamai_sensor_script(akamai_html),
         "https://cdn.bootcss.com/akam/12345/abcde_xyz.js")

    test("extract_akamai_sensor_script - empty",
         extract_akamai_sensor_script(""),
         "")

    # Test Akamai sensor data extraction
    akamai_data_html = '''
    <html>
    <script>
    var bazadebezolkohpepadr = 42;
    var _abck = "token123";
    var sensorArray = ["sensor1", "sensor2", "sensor3"];
    </script>
    </html>
    '''
    result = extract_akamai_sensor_data(akamai_data_html)
    test("extract_akamai_sensor_data - has var", 'var' in result, True)

    # Test Akamai pixel path
    akamai_pixel_html = '<script src="https://cdn.akam/98765/pixel_test"></script>'
    test("extract_akamai_pixel_path - valid",
         extract_akamai_pixel_path(akamai_pixel_html, "content"),
         "pixel_pixel_test")

    # Test Akamai SBSD parsing
    akamai_sbsd_html = '''
    <script>
    var index = 5;
    var uuid = "550e8400-e29b-41d4-a716-446655440000";
    var session_id = "sess_abc123";
    </script>
    '''
    result = parse_akamai_sbsd_data(akamai_sbsd_html)
    test("parse_akamai_sbsd_data - has index", 'index' in result, True)
    test("parse_akamai_sbsd_data - has uuid", 'uuid' in result, True)

    # =========================================================================
    section("DATADOME PARSING")
    # =========================================================================

    # Test DataDome object extraction
    datadome_html = '''
    <script>
    var dd = {
        'cid': 'captcha_id_123',
        'hsh': 'hash_value_456',
        't': 'slider',
        's': 'score_789',
        'e': 1234567890
    };
    </script>
    '''
    dd_obj = extract_datadome_object(datadome_html)
    test("extract_datadome_object - cid", dd_obj.get('cid'), 'captcha_id_123')
    test("extract_datadome_object - hsh", dd_obj.get('hsh'), 'hash_value_456')

    # Test DataDome slider URL building
    test("build_datadome_slider_url - not empty",
         len(build_datadome_slider_url(dd_obj, "", "")) > 0,
         True)

    # Test DataDome interstitial URL building
    test("build_datadome_interstitial_url - not empty",
         len(build_datadome_interstitial_url(dd_obj, "", "")) > 0,
         True)

    # Test proxy block detection
    proxy_blocked = {'t': 'bv', 'cid': 'test'}
    test("build_datadome_slider_url - proxy block",
         build_datadome_slider_url(proxy_blocked, "", ""),
         "")

    # Test DataDome image extraction
    datadome_img_html = '''
    <html>
    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
    </html>
    '''
    result = extract_datadome_captcha_images(datadome_img_html)
    test("extract_datadome_captcha_images - has data", len(result) > 0, True)

    # =========================================================================
    section("INCAPSULA PARSING")
    # =========================================================================

    # Test Incapsula challenge detection
    incapsula_html = '<html><body>Pardon Our Interruption</body></html>'
    test_true("extract_incapsula_challenge_marker - detected",
              extract_incapsula_challenge_marker(incapsula_html))

    test_false("extract_incapsula_challenge_marker - not detected",
               extract_incapsula_challenge_marker("<html></html>"))

    # Test Incapsula script path extraction
    incapsula_path_html = '''
    <html>
    <script src="(/_Incapsula_Resource/sec?abc=123)"></script>
    </html>
    '''
    result = extract_incapsula_script_paths(incapsula_path_html, "https://example.com")
    test("extract_incapsula_script_paths - returns dict", isinstance(result, dict), True)

    # Test Incapsula UTMVC path extraction
    incapsula_script = 'var path = "/_Incapsula_Resource?SWKMTFSR=1&e=12345";'
    result = extract_incapsula_utmvc_script_path(incapsula_script)
    test_not_empty("extract_incapsula_utmvc_script_path", result)

    # Test submit path generation
    submit_path = generate_incapsula_submit_path("/_Incapsula_Resource")
    test("generate_incapsula_submit_path - contains base",
         "/_Incapsula_Resource" in submit_path,
         True)

    # Test Incapsula nonce extraction
    incapsula_nonce_html = '<input name="_Incapsula_Nonce" value="nonce_abc123" />'
    test("extract_incapsula_nonce - valid",
         extract_incapsula_nonce(incapsula_nonce_html),
         "nonce_abc123")

    # =========================================================================
    section("KASADA PARSING")
    # =========================================================================

    # Test Kasada endpoints extraction
    kasada_html = '''
    <html>
    <script src="https://protection.kasada.io/c.js?target=example"></script>
    <script>
    var ips_link = "https://protection.kasada.io/ips";
    </script>
    </html>
    '''
    result = extract_kasada_endpoints(kasada_html)
    test("extract_kasada_endpoints - has script_url", 'script_url' in result, True)

    # Test Kasada challenge data extraction
    kasada_challenge_html = '''
    <html>
    <script>
    var headers = {
        'x-kpsdk-st': 'state_token_abc123',
        'x-kpsdk-ct': 'challenge_token_def456',
        'x-kpsdk-fc': 'fingerprint_cookie_789'
    };
    </script>
    </html>
    '''
    result = extract_kasada_challenge_data(kasada_challenge_html)
    test("extract_kasada_challenge_data - has st", 'st' in result, True)
    test("extract_kasada_challenge_data - has ct", 'ct' in result, True)

    # Test Kasada fingerprint extraction
    kasada_script = '''
    var fingerprint_data = {
        canvas: "canvas_fingerprint_123",
        webgl: "webgl_data_456",
        device: "device_id_789"
    };
    '''
    result = extract_kasada_fingerprint_context(kasada_script)
    test("extract_kasada_fingerprint_context - returns dict", isinstance(result, dict), True)

    # Test Kasada POW response parsing
    kasada_response = '{"st":"new_state_token","cr":"challenge_response"}'
    result = parse_kasada_pow_response(kasada_response)
    test("parse_kasada_pow_response - has st", result.get('st'), 'new_state_token')
    test("parse_kasada_pow_response - has cr", result.get('cr'), 'challenge_response')

    # =========================================================================
    section("PROTECTION DETECTION")
    # =========================================================================

    # Test Akamai detection
    test("detect_protection_system - akamai",
         detect_protection_system(akamai_html),
         "akamai")

    # Test DataDome detection
    test("detect_protection_system - datadome",
         detect_protection_system('var dd = {};'),
         "datadome")

    # Test Incapsula detection
    test("detect_protection_system - incapsula",
         detect_protection_system(incapsula_html),
         "incapsula")

    # Test Kasada detection
    test("detect_protection_system - kasada",
         detect_protection_system('x-kpsdk: token'),
         "kasada")

    # Test unknown detection
    test("detect_protection_system - unknown",
         detect_protection_system('<html><body>No protection</body></html>'),
         "unknown")

    # =========================================================================
    section("UNIFIED EXTRACTION")
    # =========================================================================

    # Test unified extraction with Akamai
    result = extract_all_protection_data(akamai_html)
    test("extract_all_protection_data - detects system", result.get('system'), 'akamai')
    test("extract_all_protection_data - has data keys", len(result) > 1, True)

    # Test unified extraction with DataDome
    result = extract_all_protection_data(datadome_html)
    test("extract_all_protection_data - datadome system", result.get('system'), 'datadome')

    # Test unified extraction with Incapsula
    result = extract_all_protection_data(incapsula_html)
    test("extract_all_protection_data - incapsula system", result.get('system'), 'incapsula')

    # Test unified extraction with Kasada
    result = extract_all_protection_data(kasada_html)
    test("extract_all_protection_data - kasada system", result.get('system'), 'kasada')

    # =========================================================================
    section("ERROR HANDLING")
    # =========================================================================

    # Test empty input handling
    test("extract_akamai_sensor_script - empty input",
         extract_akamai_sensor_script(""),
         "")

    test("extract_datadome_object - empty input",
         extract_datadome_object(""),
         {})

    test("extract_incapsula_challenge_marker - empty input",
         extract_incapsula_challenge_marker(""),
         False)

    test("extract_kasada_endpoints - empty input",
         extract_kasada_endpoints(""),
         {})

    # =========================================================================
    # Summary
    # =========================================================================

    print(f"\n{'='*60}")
    print(f" SUMMARY")
    print('='*60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    total = passed + failed
    print(f"Total:  {total}")

    if failed == 0:
        print("\nAll tests passed! ✓")
    else:
        print(f"\n{failed} test(s) failed.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
