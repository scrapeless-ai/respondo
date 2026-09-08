"""
Cryptographic Encoding, Hashing, and Utilities Module

Provides encoding, hashing, password hashing, UUID generation, random tokens, and time utilities.
Zero dependencies - uses only Python stdlib.
"""

import base64
import codecs
import hashlib
import hmac as hmac_module
import secrets
import string
import time
import calendar
import urllib.parse
import uuid as uuid_module
import zlib
from typing import Optional, Union


def _to_bytes(data: Union[str, bytes]) -> bytes:
    """Convert str or bytes to bytes using UTF-8 encoding."""
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


# =============================================================================
# Hex Encoding
# =============================================================================

def hex_encode(data: Union[str, bytes]) -> str:
    """
    Convert data to hexadecimal string.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal string, or "" on empty input
    """
    if not data:
        return ""
    return _to_bytes(data).hex()


def hex_decode(data: str) -> bytes:
    """
    Decode hexadecimal string to bytes.

    Args:
        data: Hexadecimal string

    Returns:
        Decoded bytes, or b"" on invalid input
    """
    if not data:
        return b""
    try:
        return bytes.fromhex(data)
    except Exception:
        return b""


# =============================================================================
# Base32 Encoding
# =============================================================================

def b32_encode(data: Union[str, bytes]) -> str:
    """
    Encode data using Base32 encoding.

    Base32 is often used in OTP/2FA tokens and case-insensitive contexts.

    Args:
        data: Input string or bytes

    Returns:
        Base32 encoded string (uppercase), or "" on empty input
    """
    if not data:
        return ""
    return base64.b32encode(_to_bytes(data)).decode("ascii")


def b32_decode(data: str) -> bytes:
    """
    Decode Base32 encoded string.

    Args:
        data: Base32 encoded string

    Returns:
        Decoded bytes, or b"" on invalid input
    """
    if not data:
        return b""
    try:
        # Add padding if needed
        padding = (8 - len(data) % 8) % 8
        padded = data.upper() + "=" * padding
        return base64.b32decode(padded)
    except Exception:
        return b""


# =============================================================================
# ASCII85/Base85 Encoding
# =============================================================================

def a85_encode(data: Union[str, bytes]) -> str:
    """
    Encode data using ASCII85 (Base85) encoding.

    Args:
        data: Input string or bytes

    Returns:
        ASCII85 encoded string, or "" on empty input
    """
    if not data:
        return ""
    return base64.a85encode(_to_bytes(data)).decode("ascii")


def a85_decode(data: str) -> bytes:
    """
    Decode ASCII85 (Base85) encoded string.

    Args:
        data: ASCII85 encoded string

    Returns:
        Decoded bytes, or b"" on invalid input
    """
    if not data:
        return b""
    try:
        return base64.a85decode(data)
    except Exception:
        return b""


def b85_encode(data: Union[str, bytes]) -> str:
    """
    Encode data using Base85 encoding (RFC 1924 variant).

    Args:
        data: Input string or bytes

    Returns:
        Base85 encoded string, or "" on empty input
    """
    if not data:
        return ""
    return base64.b85encode(_to_bytes(data)).decode("ascii")


def b85_decode(data: str) -> bytes:
    """
    Decode Base85 encoded string (RFC 1924 variant).

    Args:
        data: Base85 encoded string

    Returns:
        Decoded bytes, or b"" on invalid input
    """
    if not data:
        return b""
    try:
        return base64.b85decode(data)
    except Exception:
        return b""


# =============================================================================
# ROT13 Cipher
# =============================================================================

def rot13(text: str) -> str:
    """
    Apply ROT13 cipher to text.

    ROT13 replaces each letter with the 13th letter after it.
    Applying ROT13 twice returns the original text.

    Args:
        text: Input string

    Returns:
        ROT13 transformed string, or "" on empty input
    """
    if not text:
        return ""
    return codecs.encode(text, "rot_13")


# =============================================================================
# Punycode Encoding (Internationalized Domain Names)
# =============================================================================

def punycode_encode(text: str) -> str:
    """
    Encode Unicode text to Punycode (ASCII-compatible encoding).

    Used for internationalized domain names (IDN).

    Args:
        text: Unicode string

    Returns:
        Punycode encoded string, or "" on empty/error
    """
    if not text:
        return ""
    try:
        return text.encode("punycode").decode("ascii")
    except Exception:
        return ""


def punycode_decode(data: str) -> str:
    """
    Decode Punycode to Unicode text.

    Args:
        data: Punycode encoded string

    Returns:
        Decoded Unicode string, or "" on invalid input
    """
    if not data:
        return ""
    try:
        return data.encode("ascii").decode("punycode")
    except Exception:
        return ""


# =============================================================================
# URL Encoding (Percent Encoding)
# =============================================================================

def quote(text: str, safe: str = "") -> str:
    """
    URL-encode a string (percent encoding).

    Converts special characters to %XX format.

    Args:
        text: String to encode
        safe: Characters that should not be encoded (default: none)

    Returns:
        URL-encoded string, or "" on empty input
    """
    if not text:
        return ""
    return urllib.parse.quote(text, safe=safe)


def unquote(text: str) -> str:
    """
    Decode a URL-encoded string.

    Converts %XX sequences back to characters.

    Args:
        text: URL-encoded string

    Returns:
        Decoded string, or "" on empty input
    """
    if not text:
        return ""
    return urllib.parse.unquote(text)


# =============================================================================
# Hashing Functions
# =============================================================================

def _hash(algorithm: str, data: Union[str, bytes]) -> str:
    """Internal helper to compute hash with given algorithm."""
    if not data:
        return ""
    try:
        h = hashlib.new(algorithm)
        h.update(_to_bytes(data))
        return h.hexdigest()
    except Exception:
        return ""


def md5(data: Union[str, bytes]) -> str:
    """
    Compute MD5 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal MD5 hash (32 chars), or "" on empty input
    """
    return _hash("md5", data)


def sha1(data: Union[str, bytes]) -> str:
    """
    Compute SHA1 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA1 hash (40 chars), or "" on empty input
    """
    return _hash("sha1", data)


def sha256(data: Union[str, bytes]) -> str:
    """
    Compute SHA256 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA256 hash (64 chars), or "" on empty input
    """
    return _hash("sha256", data)


def sha512(data: Union[str, bytes]) -> str:
    """
    Compute SHA512 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA512 hash (128 chars), or "" on empty input
    """
    return _hash("sha512", data)


def sha224(data: Union[str, bytes]) -> str:
    """
    Compute SHA224 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA224 hash (56 chars), or "" on empty input
    """
    return _hash("sha224", data)


def sha384(data: Union[str, bytes]) -> str:
    """
    Compute SHA384 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA384 hash (96 chars), or "" on empty input
    """
    return _hash("sha384", data)


def sha3_256(data: Union[str, bytes]) -> str:
    """
    Compute SHA3-256 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA3-256 hash (64 chars), or "" on empty input
    """
    return _hash("sha3_256", data)


def sha3_512(data: Union[str, bytes]) -> str:
    """
    Compute SHA3-512 hash.

    Args:
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal SHA3-512 hash (128 chars), or "" on empty input
    """
    return _hash("sha3_512", data)


# =============================================================================
# BLAKE2 Hashing
# =============================================================================

def blake2b(data: Union[str, bytes], digest_size: int = 64) -> str:
    """
    Compute BLAKE2b hash.

    BLAKE2b is optimized for 64-bit platforms and can produce digests
    from 1 to 64 bytes.

    Args:
        data: Input string or bytes
        digest_size: Output size in bytes (1-64, default: 64)

    Returns:
        Lowercase hexadecimal BLAKE2b hash, or "" on empty input
    """
    if not data:
        return ""
    try:
        h = hashlib.blake2b(digest_size=min(max(digest_size, 1), 64))
        h.update(_to_bytes(data))
        return h.hexdigest()
    except Exception:
        return ""


def blake2s(data: Union[str, bytes], digest_size: int = 32) -> str:
    """
    Compute BLAKE2s hash.

    BLAKE2s is optimized for 32-bit platforms and can produce digests
    from 1 to 32 bytes.

    Args:
        data: Input string or bytes
        digest_size: Output size in bytes (1-32, default: 32)

    Returns:
        Lowercase hexadecimal BLAKE2s hash, or "" on empty input
    """
    if not data:
        return ""
    try:
        h = hashlib.blake2s(digest_size=min(max(digest_size, 1), 32))
        h.update(_to_bytes(data))
        return h.hexdigest()
    except Exception:
        return ""


# =============================================================================
# Checksums
# =============================================================================

def crc32(data: Union[str, bytes]) -> int:
    """
    Compute CRC32 checksum.

    Args:
        data: Input string or bytes

    Returns:
        CRC32 checksum as unsigned integer, or 0 on empty input
    """
    if not data:
        return 0
    return zlib.crc32(_to_bytes(data)) & 0xFFFFFFFF


def adler32(data: Union[str, bytes]) -> int:
    """
    Compute Adler-32 checksum.

    Adler-32 is faster than CRC32 but less reliable for small data.

    Args:
        data: Input string or bytes

    Returns:
        Adler-32 checksum as unsigned integer, or 1 on empty input
    """
    if not data:
        return 1  # Adler32 of empty data is 1
    return zlib.adler32(_to_bytes(data)) & 0xFFFFFFFF


# =============================================================================
# HMAC Functions
# =============================================================================

def hmac_sha256(key: Union[str, bytes], data: Union[str, bytes]) -> str:
    """
    Compute HMAC-SHA256.

    Args:
        key: Secret key (string or bytes)
        data: Data to authenticate (string or bytes)

    Returns:
        Lowercase hexadecimal HMAC-SHA256 (64 chars), or "" on empty input
    """
    if not key or not data:
        return ""
    try:
        return hmac_module.new(
            _to_bytes(key),
            _to_bytes(data),
            hashlib.sha256
        ).hexdigest()
    except Exception:
        return ""


def hmac_sha512(key: Union[str, bytes], data: Union[str, bytes]) -> str:
    """
    Compute HMAC-SHA512.

    Args:
        key: Secret key (string or bytes)
        data: Data to authenticate (string or bytes)

    Returns:
        Lowercase hexadecimal HMAC-SHA512 (128 chars), or "" on empty input
    """
    if not key or not data:
        return ""
    try:
        return hmac_module.new(
            _to_bytes(key),
            _to_bytes(data),
            hashlib.sha512
        ).hexdigest()
    except Exception:
        return ""


# =============================================================================
# Generic Hash Function
# =============================================================================

def hash_data(algorithm: str, data: Union[str, bytes]) -> str:
    """
    Compute hash using specified algorithm.

    Args:
        algorithm: Hash algorithm name (md5, sha1, sha256, sha512, sha224,
                   sha384, sha3_256, sha3_512, blake2b, blake2s, etc.)
        data: Input string or bytes

    Returns:
        Lowercase hexadecimal hash, or "" on invalid algorithm or empty input
    """
    return _hash(algorithm, data)


# =============================================================================
# Password Hashing (PBKDF2)
# =============================================================================

def hash_password(
    password: str,
    salt: Optional[bytes] = None,
    iterations: int = 100000,
    hash_name: str = "sha256"
) -> str:
    """
    Hash a password using PBKDF2.

    Returns a string in format: algorithm$iterations$salt$hash

    Args:
        password: Password to hash
        salt: Salt bytes (16 random bytes generated if not provided)
        iterations: Number of iterations (default: 100000)
        hash_name: Hash algorithm (default: sha256)

    Returns:
        Password hash string, or "" on empty password
    """
    if not password:
        return ""
    try:
        if salt is None:
            salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac(hash_name, password.encode("utf-8"), salt, iterations)
        salt_hex = salt.hex()
        hash_hex = dk.hex()
        return f"pbkdf2_{hash_name}${iterations}${salt_hex}${hash_hex}"
    except Exception:
        return ""


def verify_password(password: str, hash_string: str) -> bool:
    """
    Verify a password against a PBKDF2 hash string.

    Args:
        password: Password to verify
        hash_string: Hash string from hash_password()

    Returns:
        True if password matches, False otherwise
    """
    if not password or not hash_string:
        return False
    try:
        parts = hash_string.split("$")
        if len(parts) != 4:
            return False
        algorithm = parts[0]  # e.g., "pbkdf2_sha256"
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = parts[3]

        # Extract hash name from algorithm
        hash_name = algorithm.replace("pbkdf2_", "")

        dk = hashlib.pbkdf2_hmac(hash_name, password.encode("utf-8"), salt, iterations)
        return hmac_module.compare_digest(dk.hex(), expected_hash)
    except Exception:
        return False


# =============================================================================
# UUID Generation
# =============================================================================

def uuid4() -> str:
    """
    Generate a random UUID (version 4).

    Returns:
        Random UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid_module.uuid4())


def uuid5(namespace: str, name: str) -> str:
    """
    Generate a UUID based on SHA-1 hash of namespace and name (version 5).

    Args:
        namespace: Namespace UUID string or one of: "dns", "url", "oid", "x500"
        name: Name to hash within the namespace

    Returns:
        UUID string, or "" on invalid input
    """
    if not namespace or not name:
        return ""
    try:
        # Handle predefined namespaces
        ns_map = {
            "dns": uuid_module.NAMESPACE_DNS,
            "url": uuid_module.NAMESPACE_URL,
            "oid": uuid_module.NAMESPACE_OID,
            "x500": uuid_module.NAMESPACE_X500,
        }
        ns = ns_map.get(namespace.lower())
        if ns is None:
            ns = uuid_module.UUID(namespace)
        return str(uuid_module.uuid5(ns, name))
    except Exception:
        return ""


def uuid1() -> str:
    """
    Generate a UUID based on host ID and current time (version 1).

    Note: Contains MAC address, may have privacy implications.

    Returns:
        Time-based UUID string
    """
    return str(uuid_module.uuid1())


# =============================================================================
# Random Token Generation
# =============================================================================

def random_bytes(length: int = 32) -> bytes:
    """
    Generate cryptographically secure random bytes.

    Args:
        length: Number of bytes (default: 32)

    Returns:
        Random bytes
    """
    if length <= 0:
        return b""
    return secrets.token_bytes(length)


def random_hex(length: int = 32) -> str:
    """
    Generate a random hexadecimal string.

    Args:
        length: Number of hex characters (default: 32)

    Returns:
        Random hex string (lowercase)
    """
    if length <= 0:
        return ""
    # Each byte = 2 hex chars
    num_bytes = (length + 1) // 2
    return secrets.token_hex(num_bytes)[:length]


def random_string(
    length: int = 32,
    chars: str = string.ascii_letters + string.digits
) -> str:
    """
    Generate a random string from specified characters.

    Args:
        length: Number of characters (default: 32)
        chars: Character set to use (default: alphanumeric)

    Returns:
        Random string
    """
    if length <= 0 or not chars:
        return ""
    return "".join(secrets.choice(chars) for _ in range(length))


def random_urlsafe(length: int = 32) -> str:
    """
    Generate a URL-safe random string.

    Uses base64 URL-safe alphabet (A-Z, a-z, 0-9, -, _).

    Args:
        length: Approximate number of characters (default: 32)

    Returns:
        URL-safe random string
    """
    if length <= 0:
        return ""
    # token_urlsafe produces ~1.3x the bytes requested
    num_bytes = (length * 3) // 4 + 1
    return secrets.token_urlsafe(num_bytes)[:length]


# =============================================================================
# Timestamp Utilities
# =============================================================================

def timestamp() -> int:
    """
    Get current Unix timestamp (seconds since epoch).

    Returns:
        Current Unix timestamp as integer
    """
    return int(time.time())


def timestamp_ms() -> int:
    """
    Get current Unix timestamp in milliseconds.

    Returns:
        Current Unix timestamp in milliseconds
    """
    return int(time.time() * 1000)


def from_timestamp(ts: Union[int, float]) -> str:
    """
    Convert Unix timestamp to ISO 8601 string (UTC).

    Args:
        ts: Unix timestamp (seconds)

    Returns:
        ISO 8601 formatted string, or "" on invalid input
    """
    if ts is None:
        return ""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    except Exception:
        return ""


def to_timestamp(iso_string: str) -> int:
    """
    Convert ISO 8601 string to Unix timestamp.

    A trailing Z is UTC; inputs without a zone retain local-time semantics.

    Args:
        iso_string: ISO 8601 formatted string (e.g., "2024-01-15T10:30:00Z")

    Returns:
        Unix timestamp as integer, or 0 on invalid input
    """
    if not iso_string:
        return 0
    try:
        # Handle various ISO 8601 formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                parsed = time.strptime(iso_string, fmt)
                return int(calendar.timegm(parsed) if fmt.endswith("Z") else time.mktime(parsed))
            except ValueError:
                continue
        return 0
    except Exception:
        return 0


__all__ = [
    # Hex encoding
    "hex_encode",
    "hex_decode",
    # Base32 encoding
    "b32_encode",
    "b32_decode",
    # ASCII85/Base85 encoding
    "a85_encode",
    "a85_decode",
    "b85_encode",
    "b85_decode",
    # ROT13
    "rot13",
    # Punycode
    "punycode_encode",
    "punycode_decode",
    # URL encoding
    "quote",
    "unquote",
    # Common hashes
    "md5",
    "sha1",
    "sha256",
    "sha512",
    # Extended SHA
    "sha224",
    "sha384",
    "sha3_256",
    "sha3_512",
    # BLAKE2
    "blake2b",
    "blake2s",
    # Checksums
    "crc32",
    "adler32",
    # HMAC
    "hmac_sha256",
    "hmac_sha512",
    # Generic hash
    "hash_data",
    # Password hashing
    "hash_password",
    "verify_password",
    # UUID
    "uuid4",
    "uuid5",
    "uuid1",
    # Random
    "random_bytes",
    "random_hex",
    "random_string",
    "random_urlsafe",
    # Timestamps
    "timestamp",
    "timestamp_ms",
    "from_timestamp",
    "to_timestamp",
]
