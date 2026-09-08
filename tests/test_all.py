#!/usr/bin/env python3
"""
Respondo - Complete Test Suite
Tests all 100+ extraction functions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from textparse import (
    # Core text extraction
    between, betweens, between_last, between_n, between_nested,
    # Before/after extraction
    before, after, before_last, after_last,
    # Split utilities
    split_first, split_last,
    # Line-based extraction
    line_containing, lines_containing, lines_between,
    # Context extraction
    around,
    # Attribute extraction
    attr, attrs,
    # Chunk/slice utilities
    take, take_last, skip, skip_last, truncate,
    # Case conversion
    to_snake_case, to_camel_case, to_pascal_case, to_kebab_case, to_title_case,
    # String manipulation
    remove, replace_first, replace_last, pad_left, pad_right, reverse,
    # String queries
    count_occurrences, contains_all, contains_any, starts_with_any, ends_with_any,
    is_empty, is_numeric,
    # Word/sentence utilities
    words, word_count, sentences, first_word, last_word, nth_word,
    # Safe parsing
    parse_int, parse_float, parse_bool,
    # Slug/filename
    slugify, to_filename,
    # Similarity
    common_prefix, common_suffix, similarity,
    # Text cleaning
    normalize_space, strip_tags, unescape_html,
    regex_first, regex_all, parse_csrf_token,
    # Encoding
    url_encode, url_decode, b64_encode, b64_decode,
    # Validation
    is_valid_email, is_valid_url, is_valid_json,
    # Basic extraction
    extract_emails, extract_urls, extract_numbers, clean_text,
    # Social media
    extract_discord_invites, extract_telegram_links, extract_twitter_links,
    extract_youtube_links, extract_instagram_links, extract_tiktok_links,
    extract_reddit_links, extract_social_links,
    # Crypto
    extract_eth_addresses, extract_btc_addresses, extract_sol_addresses,
    extract_ens_names, extract_crypto_addresses,
    # Security
    extract_api_keys, extract_jwts, decode_jwt, extract_bearer_tokens,
    # Contact
    extract_phone_numbers, extract_dates,
    # Network
    extract_ipv4, extract_ipv6, extract_ips, extract_domains,
    extract_uuids, extract_mac_addresses,
    # API
    extract_api_endpoints, extract_graphql_endpoints, extract_websocket_urls,
    # Media
    extract_video_urls, extract_audio_urls, extract_stream_urls,
    # E-commerce
    extract_prices, extract_skus,
    # Structured data
    extract_canonical_url, extract_og_tags, extract_twitter_cards,
    extract_schema_org, extract_structured_data,
)

from botprotection import (
    # Captcha extraction
    extract_recaptcha_sitekey, extract_turnstile_sitekey, extract_hcaptcha_sitekey,
    # Captcha detection
    contains_recaptcha, contains_turnstile, contains_hcaptcha,
)

from cryptoutil import (
    # Hex encoding
    hex_encode, hex_decode,
    # Base32 encoding
    b32_encode, b32_decode,
    # ASCII85/Base85 encoding
    a85_encode, a85_decode, b85_encode, b85_decode,
    # ROT13
    rot13,
    # Punycode
    punycode_encode, punycode_decode,
    # URL encoding
    quote, unquote,
    # Common hashes
    md5, sha1, sha256, sha512,
    # Extended SHA
    sha224, sha384, sha3_256, sha3_512,
    # BLAKE2
    blake2b, blake2s,
    # Checksums
    crc32, adler32,
    # HMAC
    hmac_sha256, hmac_sha512,
    # Generic hash
    hash_data,
    # Password hashing
    hash_password, verify_password,
    # UUID
    uuid4, uuid5, uuid1,
    # Random
    random_bytes, random_hex, random_string, random_urlsafe,
    # Timestamps
    timestamp, timestamp_ms, from_timestamp, to_timestamp,
)

passed = 0
failed = 0


def extract_captcha_params(html: str) -> dict:
    """Extract all captcha parameters from HTML."""
    return {
        "recaptcha": extract_recaptcha_sitekey(html),
        "turnstile": extract_turnstile_sitekey(html),
        "hcaptcha": extract_hcaptcha_sitekey(html),
    }


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
    print("       RESPONDO - Complete Test Suite")
    print("="*60)

    # =========================================================================
    section("CORE TEXT EXTRACTION")
    # =========================================================================

    test("between - basic", between("<title>Hello</title>", "<title>", "</title>"), "Hello")
    test("between - not found", between("no match", "<", ">"), "")
    test("between - empty delimiters", between("test", "", ">"), "")

    test("betweens - multiple", betweens("[a][b][c]", "[", "]"), ["a", "b", "c"])
    test("betweens - none", betweens("no brackets", "[", "]"), [])

    test("between_last", between_last("[first][second]", "[", "]"), "second")
    test("between_n - 2nd match", between_n("<i>1</i><i>2</i><i>3</i>", "<i>", "</i>", 2), "2")
    test("between_n - out of range", between_n("<i>1</i>", "<i>", "</i>", 5), "")

    # Nested extraction
    test("between_nested - basic", between_nested("{{hello}}", "{{", "}}"), "hello")
    test("between_nested - nested", between_nested("{{outer{{inner}}end}}", "{{", "}}"), "outer{{inner}}end")
    test("between_nested - empty", between_nested("no match", "{{", "}}"), "")

    # =========================================================================
    section("BEFORE/AFTER EXTRACTION")
    # =========================================================================

    test("before - basic", before("hello:world", ":"), "hello")
    test("before - not found", before("hello", ":"), "")
    test("before - empty", before("", ":"), "")

    test("after - basic", after("hello:world", ":"), "world")
    test("after - not found", after("hello", ":"), "")
    test("after - empty", after("", ":"), "")

    test("before_last - basic", before_last("a/b/c", "/"), "a/b")
    test("before_last - single", before_last("a/b", "/"), "a")
    test("before_last - not found", before_last("abc", "/"), "")

    test("after_last - basic", after_last("a/b/c", "/"), "c")
    test("after_last - single", after_last("a/b", "/"), "b")
    test("after_last - not found", after_last("abc", "/"), "")

    # =========================================================================
    section("SPLIT UTILITIES")
    # =========================================================================

    test("split_first - basic", split_first("a:b:c", ":"), ("a", "b:c"))
    test("split_first - not found", split_first("abc", ":"), ("", ""))
    test("split_first - empty", split_first("", ":"), ("", ""))

    test("split_last - basic", split_last("a:b:c", ":"), ("a:b", "c"))
    test("split_last - single", split_last("a:b", ":"), ("a", "b"))
    test("split_last - not found", split_last("abc", ":"), ("", ""))

    # =========================================================================
    section("LINE-BASED EXTRACTION")
    # =========================================================================

    multiline = "line one\nline two with target\nline three"
    test("line_containing - found", line_containing(multiline, "target"), "line two with target")
    test("line_containing - not found", line_containing(multiline, "missing"), "")
    test("line_containing - empty", line_containing("", "target"), "")

    test("lines_containing - multiple", lines_containing("foo\nbar foo\nbaz", "foo"), ["foo", "bar foo"])
    test("lines_containing - none", lines_containing("abc", "xyz"), [])

    markers_text = "start\n---BEGIN---\nline1\nline2\n---END---\nend"
    test("lines_between - basic", lines_between(markers_text, "---BEGIN---", "---END---"), ["line1", "line2"])
    test("lines_between - not found", lines_between("no markers", "---BEGIN---", "---END---"), [])

    # =========================================================================
    section("CONTEXT EXTRACTION")
    # =========================================================================

    long_text = "The quick brown fox jumps over the lazy dog"
    test("around - basic", around(long_text, "fox", 5, 5), "rown fox jump")
    test("around - not found", around(long_text, "cat", 5, 5), "")
    test("around - edge start", around(long_text, "The", 5, 5), "The quic")
    test("around - edge end", around(long_text, "dog", 5, 5), "lazy dog")

    # =========================================================================
    section("ATTRIBUTE EXTRACTION")
    # =========================================================================

    tag = '<input type="text" name="username" value="john">'
    test("attr - basic", attr(tag, "name"), "username")
    test("attr - not found", attr(tag, "missing"), "")
    test("attr - case insensitive", attr(tag, "TYPE"), "text")

    test("attrs - basic", attrs(tag), {"type": "text", "name": "username", "value": "john"})
    test("attrs - empty", attrs("no attributes"), {})

    # =========================================================================
    section("CHUNK/SLICE UTILITIES")
    # =========================================================================

    test("take - basic", take("hello world", 5), "hello")
    test("take - larger than string", take("hi", 10), "hi")
    test("take - zero", take("hello", 0), "")
    test("take - empty", take("", 5), "")

    test("take_last - basic", take_last("hello world", 5), "world")
    test("take_last - larger than string", take_last("hi", 10), "hi")
    test("take_last - zero", take_last("hello", 0), "")

    test("skip - basic", skip("hello world", 6), "world")
    test("skip - zero", skip("hello", 0), "hello")
    test("skip - larger than string", skip("hi", 10), "")

    test("skip_last - basic", skip_last("hello world", 6), "hello")
    test("skip_last - zero", skip_last("hello", 0), "hello")
    test("skip_last - larger than string", skip_last("hi", 10), "")

    test("truncate - no truncation", truncate("hello", 10), "hello")
    test("truncate - with suffix", truncate("hello world", 8), "hello...")
    test("truncate - custom suffix", truncate("hello world", 9, ">>"), "hello w>>")
    test("truncate - empty", truncate("", 5), "")

    # =========================================================================
    section("CASE CONVERSION")
    # =========================================================================

    test("to_snake_case - camel", to_snake_case("camelCase"), "camel_case")
    test("to_snake_case - pascal", to_snake_case("PascalCase"), "pascal_case")
    test("to_snake_case - kebab", to_snake_case("kebab-case"), "kebab_case")
    test("to_snake_case - spaces", to_snake_case("hello world"), "hello_world")
    test("to_snake_case - empty", to_snake_case(""), "")

    test("to_camel_case - snake", to_camel_case("snake_case"), "snakeCase")
    test("to_camel_case - kebab", to_camel_case("kebab-case"), "kebabCase")
    test("to_camel_case - spaces", to_camel_case("hello world"), "helloWorld")
    test("to_camel_case - empty", to_camel_case(""), "")

    test("to_pascal_case - snake", to_pascal_case("snake_case"), "SnakeCase")
    test("to_pascal_case - kebab", to_pascal_case("kebab-case"), "KebabCase")
    test("to_pascal_case - empty", to_pascal_case(""), "")

    test("to_kebab_case - camel", to_kebab_case("camelCase"), "camel-case")
    test("to_kebab_case - snake", to_kebab_case("snake_case"), "snake-case")
    test("to_kebab_case - empty", to_kebab_case(""), "")

    test("to_title_case - basic", to_title_case("hello world"), "Hello World")
    test("to_title_case - empty", to_title_case(""), "")

    # =========================================================================
    section("STRING MANIPULATION")
    # =========================================================================

    test("remove - basic", remove("hello world", " "), "helloworld")
    test("remove - multiple", remove("aaa bbb aaa", "aaa"), " bbb ")
    test("remove - empty", remove("", "x"), "")

    test("replace_first - basic", replace_first("a b a", "a", "x"), "x b a")
    test("replace_first - not found", replace_first("abc", "x", "y"), "abc")

    test("replace_last - basic", replace_last("a b a", "a", "x"), "a b x")
    test("replace_last - not found", replace_last("abc", "x", "y"), "abc")

    test("pad_left - basic", pad_left("hi", 5), "   hi")
    test("pad_left - char", pad_left("hi", 5, "0"), "000hi")

    test("pad_right - basic", pad_right("hi", 5), "hi   ")
    test("pad_right - char", pad_right("hi", 5, "0"), "hi000")

    test("reverse - basic", reverse("hello"), "olleh")
    test("reverse - empty", reverse(""), "")

    # =========================================================================
    section("STRING QUERIES")
    # =========================================================================

    test("count_occurrences - basic", count_occurrences("abcabc", "abc"), 2)
    test("count_occurrences - none", count_occurrences("abc", "x"), 0)
    test("count_occurrences - empty", count_occurrences("", "x"), 0)

    test_true("contains_all - present", contains_all("hello world", "hello", "world"))
    test_false("contains_all - missing one", contains_all("hello world", "hello", "foo"))

    test_true("contains_any - one present", contains_any("hello world", "foo", "hello"))
    test_false("contains_any - none present", contains_any("hello world", "foo", "bar"))

    test_true("starts_with_any - match", starts_with_any("hello", "hi", "he", "ho"))
    test_false("starts_with_any - no match", starts_with_any("hello", "a", "b"))

    test_true("ends_with_any - match", ends_with_any("hello", "lo", "llo"))
    test_false("ends_with_any - no match", ends_with_any("hello", "x", "y"))

    test_true("is_empty - empty string", is_empty(""))
    test_true("is_empty - whitespace", is_empty("   "))
    test_false("is_empty - non-empty", is_empty("hello"))

    test_true("is_numeric - int", is_numeric("123"))
    test_true("is_numeric - float", is_numeric("12.34"))
    test_true("is_numeric - negative", is_numeric("-5"))
    test_false("is_numeric - non-numeric", is_numeric("abc"))

    # =========================================================================
    section("WORD/SENTENCE UTILITIES")
    # =========================================================================

    test("words - basic", words("hello world foo"), ["hello", "world", "foo"])
    test("words - empty", words(""), [])

    test("word_count - basic", word_count("hello world"), 2)
    test("word_count - empty", word_count(""), 0)

    test("sentences - basic", sentences("Hello. World! How?"), ["Hello.", "World!", "How?"])
    test("sentences - empty", sentences(""), [])

    test("first_word - basic", first_word("hello world"), "hello")
    test("first_word - empty", first_word(""), "")

    test("last_word - basic", last_word("hello world"), "world")
    test("last_word - empty", last_word(""), "")

    test("nth_word - basic", nth_word("one two three", 2), "two")
    test("nth_word - out of range", nth_word("hello", 5), "")

    # =========================================================================
    section("SAFE PARSING")
    # =========================================================================

    test("parse_int - valid", parse_int("42"), 42)
    test("parse_int - float", parse_int("3.7"), 3)
    test("parse_int - invalid", parse_int("abc"), 0)
    test("parse_int - default", parse_int("abc", -1), -1)

    test("parse_float - valid", parse_float("3.14"), 3.14)
    test("parse_float - int", parse_float("42"), 42.0)
    test("parse_float - invalid", parse_float("abc"), 0.0)

    test_true("parse_bool - true", parse_bool("true"))
    test_true("parse_bool - yes", parse_bool("yes"))
    test_true("parse_bool - 1", parse_bool("1"))
    test_false("parse_bool - false", parse_bool("false"))
    test_false("parse_bool - empty", parse_bool(""))

    # =========================================================================
    section("SLUG/FILENAME")
    # =========================================================================

    test("slugify - basic", slugify("Hello World!"), "hello-world")
    test("slugify - special chars", slugify("What's up?"), "whats-up")
    test("slugify - unicode", slugify("Héllo Wörld"), "hello-world")
    test("slugify - empty", slugify(""), "")

    test("to_filename - basic", to_filename("my file.txt"), "my file.txt")
    test("to_filename - invalid chars", to_filename("file:name?"), "file_name_")
    test("to_filename - empty", to_filename(""), "")

    # =========================================================================
    section("STRING SIMILARITY")
    # =========================================================================

    test("common_prefix - basic", common_prefix("hello", "help"), "hel")
    test("common_prefix - none", common_prefix("abc", "xyz"), "")
    test("common_prefix - empty", common_prefix("", "hello"), "")

    test("common_suffix - basic", common_suffix("testing", "running"), "ing")
    test("common_suffix - none", common_suffix("abc", "xyz"), "")
    test("common_suffix - empty", common_suffix("", "hello"), "")

    test("similarity - identical", similarity("hello", "hello"), 1.0)
    test("similarity - different", similarity("abc", "xyz") < 0.5, True)
    test("similarity - empty", similarity("", ""), 1.0)

    # =========================================================================
    section("TEXT CLEANING")
    # =========================================================================

    test("normalize_space", normalize_space("  hello   world  "), "hello world")
    test("strip_tags", strip_tags("<p>Hello <b>World</b></p>"), "Hello World")
    test("unescape_html", unescape_html("&lt;div&gt;"), "<div>")

    test("regex_first - with group", regex_first("Price: $42.99", r"\$([\d.]+)"), "42.99")
    test("regex_first - no match", regex_first("no price", r"\$([\d.]+)"), "")

    test("regex_all", regex_all("v1 v2 v3", r"v(\d)"), ["1", "2", "3"])

    test("parse_csrf_token", parse_csrf_token('<input name="csrf_token" value="abc123">'), "abc123")

    # =========================================================================
    section("ENCODING")
    # =========================================================================

    test("url_encode", url_encode({"q": "hello world", "page": 1}), "q=hello+world&page=1")
    test("url_decode", url_decode("a=1&b=2&b=3"), {"a": ["1"], "b": ["2", "3"]})

    test("b64_encode", b64_encode("hello"), "aGVsbG8=")
    test("b64_decode", b64_decode("aGVsbG8="), b"hello")
    test("b64_decode - empty", b64_decode(""), b"")

    # =========================================================================
    section("VALIDATION")
    # =========================================================================

    test_true("is_valid_email - valid", is_valid_email("test@example.com"))
    test_false("is_valid_email - invalid", is_valid_email("not-an-email"))

    test_true("is_valid_url - valid", is_valid_url("https://example.com"))
    test_false("is_valid_url - invalid", is_valid_url("not-a-url"))

    test_true("is_valid_json - valid", is_valid_json('{"key": "value"}'))
    test_false("is_valid_json - invalid", is_valid_json("not json"))

    # =========================================================================
    section("BASIC EXTRACTION")
    # =========================================================================

    test_not_empty("extract_emails", extract_emails("Contact: test@example.com"))
    test("extract_emails - none", extract_emails("no emails here"), [])

    test_not_empty("extract_urls", extract_urls("Visit https://example.com"))
    test("extract_urls - none", extract_urls("no urls"), [])

    test_not_empty("extract_numbers", extract_numbers("Price: $19.99"))

    test("clean_text", clean_text("  hello   world  "), "hello world")

    # =========================================================================
    section("SOCIAL MEDIA EXTRACTION")
    # =========================================================================

    test("extract_discord_invites", extract_discord_invites("Join discord.gg/abc123"), ["abc123"])
    test("extract_discord_invites - discord.com", extract_discord_invites("discord.com/invite/xyz"), ["xyz"])
    test("extract_discord_invites - none", extract_discord_invites("no discord"), [])

    test("extract_telegram_links", extract_telegram_links("Follow t.me/channel"), ["channel"])
    test("extract_telegram_links - none", extract_telegram_links("no telegram"), [])

    test_not_empty("extract_twitter_links", extract_twitter_links("Check twitter.com/user"))
    test_not_empty("extract_twitter_links - x.com", extract_twitter_links("Check x.com/user"))

    test_not_empty("extract_youtube_links", extract_youtube_links("https://youtu.be/abc123"))
    test_not_empty("extract_youtube_links - full", extract_youtube_links("https://youtube.com/watch?v=abc"))

    test_not_empty("extract_instagram_links", extract_instagram_links("instagram.com/user"))
    test_not_empty("extract_tiktok_links", extract_tiktok_links("tiktok.com/@user"))
    test_not_empty("extract_reddit_links", extract_reddit_links("reddit.com/r/python"))

    social = extract_social_links("discord.gg/test t.me/channel")
    test("extract_social_links - discord", social["discord"], ["test"])
    test("extract_social_links - telegram", social["telegram"], ["channel"])

    # =========================================================================
    section("CRYPTO/WEB3 EXTRACTION")
    # =========================================================================

    test("extract_eth_addresses",
         extract_eth_addresses("0x742d35Cc6634C0532925a3b844Bc9e7595f1dE2B"),
         ["0x742d35Cc6634C0532925a3b844Bc9e7595f1dE2B"])
    test("extract_eth_addresses - none", extract_eth_addresses("no eth"), [])

    test("extract_btc_addresses - legacy",
         extract_btc_addresses("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"),
         ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"])
    test_not_empty("extract_btc_addresses - bech32",
         extract_btc_addresses("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"))

    test("extract_ens_names", extract_ens_names("vitalik.eth"), ["vitalik.eth"])
    test("extract_ens_names - multiple", extract_ens_names("alice.eth bob.eth"), ["alice.eth", "bob.eth"])

    crypto = extract_crypto_addresses("0x742d35Cc6634C0532925a3b844Bc9e7595f1dE2B vitalik.eth")
    test_not_empty("extract_crypto_addresses - eth", crypto["eth"])
    test_not_empty("extract_crypto_addresses - ens", crypto["ens"])

    # =========================================================================
    section("SECURITY TOKEN EXTRACTION")
    # =========================================================================

    keys = extract_api_keys("sk-1234567890abcdefghijklmnopqrstuvwxyz1234")
    test_not_empty("extract_api_keys - openai", keys)
    test("extract_api_keys - type", keys[0]["type"] if keys else None, "openai")

    keys_aws = extract_api_keys("AKIAIOSFODNN7EXAMPLE")
    test_not_empty("extract_api_keys - aws", keys_aws)

    keys_github = extract_api_keys("ghp_1234567890abcdefghijklmnopqrstuvwxyz")
    test_not_empty("extract_api_keys - github", keys_github)

    test("extract_api_keys - none", extract_api_keys("no keys"), [])

    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    test("extract_jwts", extract_jwts(f"token={jwt}"), [jwt])
    test("extract_jwts - none", extract_jwts("no jwt"), [])

    decoded = decode_jwt(jwt)
    test("decode_jwt - header alg", decoded["header"]["alg"] if decoded else None, "HS256")
    test("decode_jwt - payload sub", decoded["payload"]["sub"] if decoded else None, "1234567890")
    test("decode_jwt - invalid", decode_jwt("invalid"), None)

    test("extract_bearer_tokens", extract_bearer_tokens("Bearer abc123"), ["abc123"])
    test("extract_bearer_tokens - none", extract_bearer_tokens("no bearer"), [])

    # =========================================================================
    section("CONTACT INFO EXTRACTION")
    # =========================================================================

    test_not_empty("extract_phone_numbers - US", extract_phone_numbers("+1 (555) 123-4567"))
    test_not_empty("extract_phone_numbers - simple", extract_phone_numbers("555-123-4567"))
    test("extract_phone_numbers - none", extract_phone_numbers("no phone"), [])

    test_not_empty("extract_dates - ISO", extract_dates("2024-01-15"))
    test_not_empty("extract_dates - US", extract_dates("01/15/2024"))
    test_not_empty("extract_dates - long", extract_dates("January 15, 2024"))
    test("extract_dates - none", extract_dates("no dates"), [])

    # =========================================================================
    section("CAPTCHA EXTRACTION")
    # =========================================================================

    recaptcha_html = '<div class="g-recaptcha" data-sitekey="6LcxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAA"></div>'
    test("extract_recaptcha_sitekey", extract_recaptcha_sitekey(recaptcha_html), ["6LcxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAA"])

    turnstile_html = '<div class="cf-turnstile" data-sitekey="0x4AAAAAAADnPIDROrmt1Wwj"></div>'
    test("extract_turnstile_sitekey", extract_turnstile_sitekey(turnstile_html), ["0x4AAAAAAADnPIDROrmt1Wwj"])

    hcaptcha_html = '<div class="h-captcha" data-sitekey="10000000-ffff-ffff-ffff-000000000001"></div>'
    test("extract_hcaptcha_sitekey", extract_hcaptcha_sitekey(hcaptcha_html), ["10000000-ffff-ffff-ffff-000000000001"])

    params = extract_captcha_params(recaptcha_html)
    test_not_empty("extract_captcha_params - recaptcha", params["recaptcha"])

    # =========================================================================
    section("CAPTCHA DETECTION")
    # =========================================================================

    test_true("contains_recaptcha - class", contains_recaptcha('<div class="g-recaptcha"></div>'))
    test_true("contains_recaptcha - script", contains_recaptcha('google.com/recaptcha/api.js'))
    test_false("contains_recaptcha - none", contains_recaptcha('<div>no captcha</div>'))

    test_true("contains_turnstile", contains_turnstile('<div class="cf-turnstile"></div>'))
    test_false("contains_turnstile - none", contains_turnstile('<div>nothing</div>'))

    test_true("contains_hcaptcha", contains_hcaptcha('<div class="h-captcha"></div>'))

    # =========================================================================
    section("NETWORK/IDENTIFIER EXTRACTION")
    # =========================================================================

    test("extract_ipv4", extract_ipv4("192.168.1.1 and 10.0.0.1"), ["192.168.1.1", "10.0.0.1"])
    test("extract_ipv4 - none", extract_ipv4("no ips"), [])

    test_not_empty("extract_ipv6", extract_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334"))

    test("extract_ips - combined", len(extract_ips("192.168.1.1")) > 0, True)

    test("extract_domains", extract_domains("example.com and test.org"), ["example.com", "test.org"])
    test("extract_domains - none", extract_domains("no domains"), [])

    test("extract_uuids", extract_uuids("550e8400-e29b-41d4-a716-446655440000"),
         ["550e8400-e29b-41d4-a716-446655440000"])

    test("extract_mac_addresses", extract_mac_addresses("00:1A:2B:3C:4D:5E"), ["00:1A:2B:3C:4D:5E"])

    # =========================================================================
    section("API/ENDPOINT EXTRACTION")
    # =========================================================================

    test("extract_api_endpoints", extract_api_endpoints('"/api/v1/users"'), ["/api/v1/users"])
    test_not_empty("extract_api_endpoints - full url",
         extract_api_endpoints("https://api.example.com/api/v2/data"))

    test("extract_graphql_endpoints", extract_graphql_endpoints('"/graphql"'), ["/graphql"])

    test("extract_websocket_urls", extract_websocket_urls("wss://example.com/socket"),
         ["wss://example.com/socket"])
    test("extract_websocket_urls - ws", extract_websocket_urls("ws://localhost:8080"),
         ["ws://localhost:8080"])

    # =========================================================================
    section("MEDIA URL EXTRACTION")
    # =========================================================================

    test("extract_video_urls - mp4", extract_video_urls("https://cdn.com/video.mp4"),
         ["https://cdn.com/video.mp4"])
    test_not_empty("extract_video_urls - m3u8", extract_video_urls("https://cdn.com/playlist.m3u8"))

    test("extract_audio_urls - mp3", extract_audio_urls("https://cdn.com/song.mp3"),
         ["https://cdn.com/song.mp3"])

    test_not_empty("extract_stream_urls", extract_stream_urls("https://cdn.com/playlist.m3u8"))

    # =========================================================================
    section("E-COMMERCE EXTRACTION")
    # =========================================================================

    prices = extract_prices("$19.99")
    test_not_empty("extract_prices - USD", prices)
    test("extract_prices - value", prices[0]["value"] if prices else None, 19.99)
    test("extract_prices - currency", prices[0]["currency"] if prices else None, "USD")

    prices_eur = extract_prices("EUR 29.99")
    test("extract_prices - EUR currency", prices_eur[0]["currency"] if prices_eur else None, "EUR")

    test("extract_skus", extract_skus("SKU: ABC-12345"), ["ABC-12345"])
    test("extract_skus - none", extract_skus("no sku"), [])

    # =========================================================================
    section("STRUCTURED DATA EXTRACTION")
    # =========================================================================

    html = '''
    <link rel="canonical" href="https://example.com/page">
    <meta property="og:title" content="My Page">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta name="twitter:card" content="summary">
    <script type="application/ld+json">{"@type": "Product", "name": "Widget"}</script>
    '''

    test("extract_canonical_url", extract_canonical_url(html), "https://example.com/page")
    test("extract_canonical_url - none", extract_canonical_url("<div>no canonical</div>"), "")

    og = extract_og_tags(html)
    test("extract_og_tags - title", og.get("title"), "My Page")
    test("extract_og_tags - image", og.get("image"), "https://example.com/image.jpg")

    twitter = extract_twitter_cards(html)
    test("extract_twitter_cards - card", twitter.get("card"), "summary")

    schema = extract_schema_org(html)
    test_not_empty("extract_schema_org", schema)
    test("extract_schema_org - type", schema[0].get("@type") if schema else None, "Product")

    structured = extract_structured_data(html)
    test("extract_structured_data - has canonical", structured["canonical"], "https://example.com/page")
    test_not_empty("extract_structured_data - has og", structured["og"])

    # =========================================================================
    section("CRYPTO - ENCODING")
    # =========================================================================

    # Hex encoding
    test("hex_encode - string", hex_encode("hello"), "68656c6c6f")
    test("hex_encode - bytes", hex_encode(b"hello"), "68656c6c6f")
    test("hex_encode - empty", hex_encode(""), "")

    test("hex_decode - valid", hex_decode("68656c6c6f"), b"hello")
    test("hex_decode - empty", hex_decode(""), b"")
    test("hex_decode - invalid", hex_decode("zzzz"), b"")

    # ASCII85 encoding
    test_not_empty("a85_encode - string", a85_encode("hello"))
    test("a85_encode - empty", a85_encode(""), "")
    test("a85_decode - roundtrip", a85_decode(a85_encode("hello")), b"hello")
    test("a85_decode - empty", a85_decode(""), b"")

    # ROT13
    test("rot13 - basic", rot13("hello"), "uryyb")
    test("rot13 - roundtrip", rot13(rot13("hello")), "hello")
    test("rot13 - empty", rot13(""), "")
    test("rot13 - mixed", rot13("Hello World 123"), "Uryyb Jbeyq 123")

    # =========================================================================
    section("CRYPTO - HASHING")
    # =========================================================================

    # MD5
    test("md5 - basic", md5("hello"), "5d41402abc4b2a76b9719d911017c592")
    test("md5 - bytes", md5(b"hello"), "5d41402abc4b2a76b9719d911017c592")
    test("md5 - empty", md5(""), "")

    # SHA1
    test("sha1 - basic", sha1("hello"), "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d")
    test("sha1 - empty", sha1(""), "")

    # SHA256
    test("sha256 - basic", sha256("hello"), "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
    test("sha256 - empty", sha256(""), "")

    # SHA512
    test_not_empty("sha512 - basic", sha512("hello"))
    test("sha512 - empty", sha512(""), "")

    # Extended SHA
    test_not_empty("sha224 - basic", sha224("hello"))
    test_not_empty("sha384 - basic", sha384("hello"))
    test_not_empty("sha3_256 - basic", sha3_256("hello"))
    test_not_empty("sha3_512 - basic", sha3_512("hello"))

    # Generic hash
    test("hash_data - md5", hash_data("md5", "hello"), md5("hello"))
    test("hash_data - sha256", hash_data("sha256", "hello"), sha256("hello"))
    test("hash_data - invalid algo", hash_data("invalid_algo", "hello"), "")
    test("hash_data - empty", hash_data("md5", ""), "")

    # =========================================================================
    section("CRYPTO - HMAC")
    # =========================================================================

    test_not_empty("hmac_sha256 - basic", hmac_sha256("secret", "message"))
    test("hmac_sha256 - known value", hmac_sha256("key", "The quick brown fox jumps over the lazy dog"),
         "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8")
    test("hmac_sha256 - empty key", hmac_sha256("", "message"), "")
    test("hmac_sha256 - empty data", hmac_sha256("key", ""), "")

    test_not_empty("hmac_sha512 - basic", hmac_sha512("secret", "message"))
    test("hmac_sha512 - empty key", hmac_sha512("", "message"), "")

    # =========================================================================
    section("CRYPTO - BASE32 ENCODING")
    # =========================================================================

    test("b32_encode - basic", b32_encode("hello"), "NBSWY3DP")
    test("b32_encode - empty", b32_encode(""), "")
    test("b32_decode - basic", b32_decode("NBSWY3DP"), b"hello")
    test("b32_decode - empty", b32_decode(""), b"")
    test("b32_decode - roundtrip", b32_decode(b32_encode("test")), b"test")

    # =========================================================================
    section("CRYPTO - BASE85 ENCODING")
    # =========================================================================

    test_not_empty("b85_encode - basic", b85_encode("hello"))
    test("b85_encode - empty", b85_encode(""), "")
    test("b85_decode - roundtrip", b85_decode(b85_encode("hello")), b"hello")
    test("b85_decode - empty", b85_decode(""), b"")

    # =========================================================================
    section("CRYPTO - PUNYCODE ENCODING")
    # =========================================================================

    test("punycode_encode - ascii", punycode_encode("hello"), "hello-")
    test("punycode_encode - unicode", punycode_encode("münchen"), "mnchen-3ya")
    test("punycode_encode - empty", punycode_encode(""), "")
    test("punycode_decode - ascii", punycode_decode("hello-"), "hello")
    test("punycode_decode - unicode", punycode_decode("mnchen-3ya"), "münchen")
    test("punycode_decode - empty", punycode_decode(""), "")

    # =========================================================================
    section("CRYPTO - URL ENCODING (QUOTE)")
    # =========================================================================

    test("quote - basic", quote("hello world"), "hello%20world")
    test("quote - special chars", quote("a=1&b=2"), "a%3D1%26b%3D2")
    test("quote - empty", quote(""), "")
    test("quote - with safe", quote("a/b/c", safe="/"), "a/b/c")

    test("unquote - basic", unquote("hello%20world"), "hello world")
    test("unquote - special chars", unquote("a%3D1%26b%3D2"), "a=1&b=2")
    test("unquote - empty", unquote(""), "")

    # =========================================================================
    section("CRYPTO - BLAKE2 HASHING")
    # =========================================================================

    test_not_empty("blake2b - basic", blake2b("hello"))
    test("blake2b - empty", blake2b(""), "")
    test("blake2b - custom size", len(blake2b("hello", 32)), 64)  # 32 bytes = 64 hex chars

    test_not_empty("blake2s - basic", blake2s("hello"))
    test("blake2s - empty", blake2s(""), "")
    test("blake2s - custom size", len(blake2s("hello", 16)), 32)  # 16 bytes = 32 hex chars

    # =========================================================================
    section("CRYPTO - CHECKSUMS")
    # =========================================================================

    test("crc32 - basic", crc32("hello"), 907060870)
    test("crc32 - empty", crc32(""), 0)
    test("crc32 - bytes", crc32(b"hello"), 907060870)

    test("adler32 - basic", adler32("hello"), 103547413)
    test("adler32 - empty", adler32(""), 1)  # Adler32 of empty is 1
    test("adler32 - bytes", adler32(b"hello"), 103547413)

    # =========================================================================
    section("CRYPTO - PASSWORD HASHING")
    # =========================================================================

    pw_hash = hash_password("mysecretpassword")
    test_not_empty("hash_password - basic", pw_hash)
    test("hash_password - format", pw_hash.startswith("pbkdf2_sha256$"), True)
    test("hash_password - empty", hash_password(""), "")

    test_true("verify_password - correct", verify_password("mysecretpassword", pw_hash))
    test_false("verify_password - wrong password", verify_password("wrongpassword", pw_hash))
    test_false("verify_password - empty password", verify_password("", pw_hash))
    test_false("verify_password - empty hash", verify_password("password", ""))
    test_false("verify_password - invalid hash", verify_password("password", "invalid$hash"))

    # =========================================================================
    section("CRYPTO - UUID GENERATION")
    # =========================================================================

    u4 = uuid4()
    test_not_empty("uuid4 - generates", u4)
    test("uuid4 - format", len(u4), 36)  # UUID format: 8-4-4-4-12 = 36 chars

    test("uuid5 - dns namespace", len(uuid5("dns", "example.com")), 36)
    test("uuid5 - url namespace", len(uuid5("url", "https://example.com")), 36)
    test("uuid5 - deterministic", uuid5("dns", "test"), uuid5("dns", "test"))  # Same input = same output
    test("uuid5 - empty namespace", uuid5("", "test"), "")
    test("uuid5 - empty name", uuid5("dns", ""), "")

    u1 = uuid1()
    test_not_empty("uuid1 - generates", u1)
    test("uuid1 - format", len(u1), 36)

    # =========================================================================
    section("CRYPTO - RANDOM GENERATION")
    # =========================================================================

    rb = random_bytes(16)
    test("random_bytes - length", len(rb), 16)
    test("random_bytes - type", isinstance(rb, bytes), True)
    test("random_bytes - zero length", random_bytes(0), b"")

    rh = random_hex(32)
    test("random_hex - length", len(rh), 32)
    test("random_hex - valid hex", all(c in "0123456789abcdef" for c in rh), True)
    test("random_hex - zero length", random_hex(0), "")

    rs = random_string(20)
    test("random_string - length", len(rs), 20)
    test("random_string - zero length", random_string(0), "")
    test("random_string - custom chars", all(c in "abc" for c in random_string(10, "abc")), True)

    ru = random_urlsafe(24)
    test("random_urlsafe - length", len(ru), 24)
    test("random_urlsafe - zero length", random_urlsafe(0), "")

    # =========================================================================
    section("CRYPTO - TIMESTAMPS")
    # =========================================================================

    ts = timestamp()
    test("timestamp - is int", isinstance(ts, int), True)
    test("timestamp - reasonable value", ts > 1700000000, True)  # After 2023

    ts_ms = timestamp_ms()
    test("timestamp_ms - is int", isinstance(ts_ms, int), True)
    test("timestamp_ms - is milliseconds", ts_ms > ts * 1000 - 1000, True)

    test("from_timestamp - basic", from_timestamp(0), "1970-01-01T00:00:00Z")
    test("from_timestamp - date", from_timestamp(1705320000), "2024-01-15T12:00:00Z")
    test("from_timestamp - None", from_timestamp(None), "")

    test("to_timestamp - ISO format", to_timestamp("2024-01-15T12:00:00Z") > 0, True)
    test("to_timestamp - date only", to_timestamp("2024-01-15") > 0, True)
    test("to_timestamp - empty", to_timestamp(""), 0)
    test("to_timestamp - invalid", to_timestamp("not-a-date"), 0)

    # =========================================================================
    # RESULTS
    # =========================================================================
    print("\n" + "="*60)
    print(f"       TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n  ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n  {failed} TESTS FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
