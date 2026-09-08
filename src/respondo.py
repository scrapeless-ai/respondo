from _respondo_version import __version__
from textparse import (
    # String between
    between,
    betweens,
    between_last,
    between_n,
    between_nested,
    # Before/after extraction
    before,
    after,
    before_last,
    after_last,
    # Split utilities
    split_first,
    split_last,
    # Line-based extraction
    line_containing,
    lines_containing,
    lines_between,
    # Context extraction
    around,
    # Attribute extraction
    attr,
    attrs,
    # Chunk/slice utilities
    take,
    take_last,
    skip,
    skip_last,
    truncate,
    # Case conversion
    to_snake_case,
    to_camel_case,
    to_pascal_case,
    to_kebab_case,
    to_title_case,
    # String manipulation
    remove,
    replace_first,
    replace_last,
    pad_left,
    pad_right,
    reverse,
    # String queries
    count_occurrences,
    contains_all,
    contains_any,
    starts_with_any,
    ends_with_any,
    is_empty,
    is_numeric,
    # Word/sentence utilities
    words,
    word_count,
    sentences,
    first_word,
    last_word,
    nth_word,
    # Safe parsing
    parse_int,
    parse_float,
    parse_bool,
    # Slug/filename
    slugify,
    to_filename,
    # String similarity
    common_prefix,
    common_suffix,
    similarity,
    # Text cleaning
    normalize_space,
    strip_tags,
    unescape_html,
    regex_first,
    regex_all,
    parse_csrf_token,
    url_encode,
    url_decode,
    b64_encode,
    b64_decode,
    # Validation
    is_valid_email,
    is_valid_url,
    is_valid_json,
    # Text extraction
    extract_emails,
    extract_urls,
    extract_numbers,
    clean_text,
    # Social media extraction
    extract_discord_invites,
    extract_telegram_links,
    extract_twitter_links,
    extract_youtube_links,
    extract_instagram_links,
    extract_tiktok_links,
    extract_reddit_links,
    extract_social_links,
    # Crypto extraction
    extract_eth_addresses,
    extract_btc_addresses,
    extract_sol_addresses,
    extract_ens_names,
    extract_crypto_addresses,
    # Security extraction
    extract_api_keys,
    extract_jwts,
    decode_jwt,
    extract_bearer_tokens,
    # Contact extraction
    extract_phone_numbers,
    extract_dates,
    # Network/Identifiers
    extract_ipv4,
    extract_ipv6,
    extract_ips,
    extract_domains,
    extract_uuids,
    extract_mac_addresses,
    # API/Endpoints
    extract_api_endpoints,
    extract_graphql_endpoints,
    extract_websocket_urls,
    # Media
    extract_video_urls,
    extract_audio_urls,
    extract_stream_urls,
    # E-commerce
    extract_prices,
    extract_skus,
    # Structured data
    extract_canonical_url,
    extract_og_tags,
    extract_twitter_cards,
    extract_schema_org,
    extract_structured_data,
)
from jsonparse import find_first_json, find_all_json, json_get, json_query
from jsonparse import (
    csv_to_records, iter_jsonl, json_flatten, json_merge_patch, json_pointer,
    json_project, jsonl_dumps, records_to_csv,
)
from responseutil import Response, HTTPStatusError
from webparse import normalize_url, update_url_query, parse_feed, parse_sitemap
from htmlparse import (
    select_html,
    extract_records,
    strip_scripts_styles,
    get_text,
    extract_links,
    extract_forms,
    extract_tables,
    json_in_html,
    extract_meta,
    extract_images,
    html_to_markdown,
    extract_headings,
    extract_link_details,
    extract_page,
)
from ai import AIError, parse_ai, parse_ai_json, list_providers
from botprotection import (
    # Captcha extraction
    extract_recaptcha_sitekey,
    extract_turnstile_sitekey,
    extract_hcaptcha_sitekey,
    # Captcha detection
    contains_recaptcha,
    contains_turnstile,
    contains_hcaptcha,
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
    detect_all_protection_systems,
    extract_all_protection_data,
)
from cryptoutil import (
    # Hex encoding
    hex_encode,
    hex_decode,
    # Base32 encoding
    b32_encode,
    b32_decode,
    # ASCII85/Base85 encoding
    a85_encode,
    a85_decode,
    b85_encode,
    b85_decode,
    # ROT13
    rot13,
    # Punycode
    punycode_encode,
    punycode_decode,
    # URL encoding
    quote,
    unquote,
    # Common hashes
    md5,
    sha1,
    sha256,
    sha512,
    # Extended SHA
    sha224,
    sha384,
    sha3_256,
    sha3_512,
    # BLAKE2
    blake2b,
    blake2s,
    # Checksums
    crc32,
    adler32,
    # HMAC
    hmac_sha256,
    hmac_sha512,
    # Generic hash
    hash_data,
    # Password hashing
    hash_password,
    verify_password,
    # UUID
    uuid4,
    uuid5,
    uuid1,
    # Random
    random_bytes,
    random_hex,
    random_string,
    random_urlsafe,
    # Timestamps
    timestamp,
    timestamp_ms,
    from_timestamp,
    to_timestamp,
)


def extract_captcha_params(html: str) -> dict:
    """Extract all captcha parameters from HTML."""
    return {
        "recaptcha": extract_recaptcha_sitekey(html),
        "turnstile": extract_turnstile_sitekey(html),
        "hcaptcha": extract_hcaptcha_sitekey(html),
    }


__all__ = [
    "__version__",
    "HTTPStatusError",
    "normalize_url", "update_url_query", "parse_feed", "parse_sitemap",
    "select_html", "extract_records",
    "json_pointer", "json_flatten", "json_merge_patch", "json_project",
    "iter_jsonl", "jsonl_dumps", "records_to_csv", "csv_to_records",
    # String between
    "between",
    "betweens",
    "between_last",
    "between_n",
    "between_nested",
    # Before/after extraction
    "before",
    "after",
    "before_last",
    "after_last",
    # Split utilities
    "split_first",
    "split_last",
    # Line-based extraction
    "line_containing",
    "lines_containing",
    "lines_between",
    # Context extraction
    "around",
    # Attribute extraction
    "attr",
    "attrs",
    # Chunk/slice utilities
    "take",
    "take_last",
    "skip",
    "skip_last",
    "truncate",
    # Case conversion
    "to_snake_case",
    "to_camel_case",
    "to_pascal_case",
    "to_kebab_case",
    "to_title_case",
    # String manipulation
    "remove",
    "replace_first",
    "replace_last",
    "pad_left",
    "pad_right",
    "reverse",
    # String queries
    "count_occurrences",
    "contains_all",
    "contains_any",
    "starts_with_any",
    "ends_with_any",
    "is_empty",
    "is_numeric",
    # Word/sentence utilities
    "words",
    "word_count",
    "sentences",
    "first_word",
    "last_word",
    "nth_word",
    # Safe parsing
    "parse_int",
    "parse_float",
    "parse_bool",
    # Slug/filename
    "slugify",
    "to_filename",
    # String similarity
    "common_prefix",
    "common_suffix",
    "similarity",
    # Text cleaning
    "normalize_space",
    "strip_tags",
    "unescape_html",
    "regex_first",
    "regex_all",
    "clean_text",
    # Validation
    "is_valid_email",
    "is_valid_url",
    "is_valid_json",
    # Text extraction
    "extract_emails",
    "extract_urls",
    "extract_numbers",
    # Encoding
    "parse_csrf_token",
    "url_encode",
    "url_decode",
    "b64_encode",
    "b64_decode",
    # Social media extraction
    "extract_discord_invites",
    "extract_telegram_links",
    "extract_twitter_links",
    "extract_youtube_links",
    "extract_instagram_links",
    "extract_tiktok_links",
    "extract_reddit_links",
    "extract_social_links",
    # Crypto extraction
    "extract_eth_addresses",
    "extract_btc_addresses",
    "extract_sol_addresses",
    "extract_ens_names",
    "extract_crypto_addresses",
    # Security extraction
    "extract_api_keys",
    "extract_jwts",
    "decode_jwt",
    "extract_bearer_tokens",
    # Contact extraction
    "extract_phone_numbers",
    "extract_dates",
    # Captcha extraction
    "extract_recaptcha_sitekey",
    "extract_turnstile_sitekey",
    "extract_hcaptcha_sitekey",
    "extract_captcha_params",
    # Captcha detection
    "contains_recaptcha",
    "contains_turnstile",
    "contains_hcaptcha",
    # Network/Identifiers
    "extract_ipv4",
    "extract_ipv6",
    "extract_ips",
    "extract_domains",
    "extract_uuids",
    "extract_mac_addresses",
    # API/Endpoints
    "extract_api_endpoints",
    "extract_graphql_endpoints",
    "extract_websocket_urls",
    # Media
    "extract_video_urls",
    "extract_audio_urls",
    "extract_stream_urls",
    # E-commerce
    "extract_prices",
    "extract_skus",
    # Structured data
    "extract_canonical_url",
    "extract_og_tags",
    "extract_twitter_cards",
    "extract_schema_org",
    "extract_structured_data",
    # Response
    "Response",
    # HTML
    "strip_scripts_styles",
    "get_text",
    "extract_links",
    "extract_forms",
    "extract_tables",
    "extract_meta",
    "extract_images",
    "html_to_markdown",
    "json_in_html",
    "extract_headings",
    "extract_link_details",
    "extract_page",
    # JSON
    "find_first_json",
    "find_all_json",
    "json_get",
    "json_query",
    # AI
    "parse_ai",
    "AIError",
    "parse_ai_json",
    "list_providers",
    # Bot Protection - Akamai
    "extract_akamai_sensor_script",
    "extract_akamai_sensor_data",
    "extract_akamai_pixel_path",
    "parse_akamai_sbsd_data",
    # Bot Protection - DataDome
    "extract_datadome_object",
    "build_datadome_slider_url",
    "build_datadome_interstitial_url",
    "extract_datadome_captcha_images",
    # Bot Protection - Incapsula
    "extract_incapsula_challenge_marker",
    "extract_incapsula_script_paths",
    "extract_incapsula_utmvc_script_path",
    "generate_incapsula_submit_path",
    "extract_incapsula_nonce",
    # Bot Protection - Kasada
    "extract_kasada_endpoints",
    "extract_kasada_challenge_data",
    "extract_kasada_fingerprint_context",
    "parse_kasada_pow_response",
    # Bot Protection - Detection
    "detect_protection_system",
    "detect_all_protection_systems",
    "extract_all_protection_data",
    # Crypto - Hex encoding
    "hex_encode",
    "hex_decode",
    # Crypto - Base32 encoding
    "b32_encode",
    "b32_decode",
    # Crypto - ASCII85/Base85 encoding
    "a85_encode",
    "a85_decode",
    "b85_encode",
    "b85_decode",
    # Crypto - ROT13
    "rot13",
    # Crypto - Punycode
    "punycode_encode",
    "punycode_decode",
    # Crypto - URL encoding
    "quote",
    "unquote",
    # Crypto - Common hashes
    "md5",
    "sha1",
    "sha256",
    "sha512",
    # Crypto - Extended SHA
    "sha224",
    "sha384",
    "sha3_256",
    "sha3_512",
    # Crypto - BLAKE2
    "blake2b",
    "blake2s",
    # Crypto - Checksums
    "crc32",
    "adler32",
    # Crypto - HMAC
    "hmac_sha256",
    "hmac_sha512",
    # Crypto - Generic hash
    "hash_data",
    # Crypto - Password hashing
    "hash_password",
    "verify_password",
    # Crypto - UUID
    "uuid4",
    "uuid5",
    "uuid1",
    # Crypto - Random
    "random_bytes",
    "random_hex",
    "random_string",
    "random_urlsafe",
    # Crypto - Timestamps
    "timestamp",
    "timestamp_ms",
    "from_timestamp",
    "to_timestamp",
]


if __name__ == "__main__":
    from respondo_cli import main

    raise SystemExit(main())
