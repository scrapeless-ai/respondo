"""
Text Parsing and Extraction Module

Provides text manipulation, validation, and extraction utilities for web scraping.
Zero dependencies - uses only Python stdlib.
"""

from __future__ import annotations

import base64
import html
import json
import re
import unicodedata
import urllib.parse
from typing import Any, Mapping, Sequence


# =============================================================================
# String Between Functions
# =============================================================================

def between(s: str, left: str, right: str) -> str:
    """Extract text between two delimiters."""
    if not left or not right:
        return ""
    start = s.find(left)
    if start == -1:
        return ""
    start += len(left)
    end = s.find(right, start)
    if end == -1:
        return ""
    return s[start:end]


def betweens(s: str, left: str, right: str) -> list[str]:
    """Extract all occurrences of text between two delimiters."""
    if not left or not right:
        return []
    res: list[str] = []
    pos = 0
    while True:
        start = s.find(left, pos)
        if start == -1:
            break
        start += len(left)
        end = s.find(right, start)
        if end == -1:
            break
        res.append(s[start:end])
        pos = end + len(right)
    return res


def between_last(s: str, left: str, right: str) -> str:
    """Extract text between last occurrence of delimiters."""
    if not left or not right:
        return ""
    start = s.rfind(left)
    if start == -1:
        return ""
    start += len(left)
    end = s.find(right, start)
    if end == -1:
        return ""
    return s[start:end]


def between_n(s: str, left: str, right: str, n: int) -> str:
    """Extract nth occurrence of text between delimiters."""
    if n < 1:
        return ""
    matches = betweens(s, left, right)
    if n - 1 < len(matches):
        return matches[n - 1]
    return ""


def between_nested(s: str, left: str, right: str) -> str:
    """
    Extract text between nested delimiters.

    Handles matching pairs like {{...}}, [[...]], etc.
    Returns the content of the outermost matched pair.

    Args:
        s: Source string
        left: Opening delimiter (e.g., "{{" or "[[")
        right: Closing delimiter (e.g., "}}" or "]]")

    Returns:
        Text between matched delimiters, or "" if not found
    """
    if not s or not left or not right:
        return ""
    start = s.find(left)
    if start == -1:
        return ""
    depth = 1
    pos = start + len(left)
    while pos < len(s) and depth > 0:
        # Check for closing delimiter first (handles case where left == right)
        if s[pos:pos + len(right)] == right:
            depth -= 1
            if depth == 0:
                return s[start + len(left):pos]
            pos += len(right)
        elif s[pos:pos + len(left)] == left:
            depth += 1
            pos += len(left)
        else:
            pos += 1
    return ""


# =============================================================================
# Before/After Extraction
# =============================================================================

def before(s: str, delimiter: str) -> str:
    """
    Extract text before the first occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to search for

    Returns:
        Text before delimiter, or "" if not found
    """
    if not s or not delimiter:
        return ""
    idx = s.find(delimiter)
    if idx == -1:
        return ""
    return s[:idx]


def after(s: str, delimiter: str) -> str:
    """
    Extract text after the first occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to search for

    Returns:
        Text after delimiter, or "" if not found
    """
    if not s or not delimiter:
        return ""
    idx = s.find(delimiter)
    if idx == -1:
        return ""
    return s[idx + len(delimiter):]


def before_last(s: str, delimiter: str) -> str:
    """
    Extract text before the last occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to search for

    Returns:
        Text before last delimiter, or "" if not found
    """
    if not s or not delimiter:
        return ""
    idx = s.rfind(delimiter)
    if idx == -1:
        return ""
    return s[:idx]


def after_last(s: str, delimiter: str) -> str:
    """
    Extract text after the last occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to search for

    Returns:
        Text after last delimiter, or "" if not found
    """
    if not s or not delimiter:
        return ""
    idx = s.rfind(delimiter)
    if idx == -1:
        return ""
    return s[idx + len(delimiter):]


# =============================================================================
# Split Utilities
# =============================================================================

def split_first(s: str, delimiter: str) -> tuple[str, str]:
    """
    Split string at first occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to split on

    Returns:
        Tuple of (before, after), or ("", "") if not found
    """
    if not s or not delimiter:
        return ("", "")
    idx = s.find(delimiter)
    if idx == -1:
        return ("", "")
    return (s[:idx], s[idx + len(delimiter):])


def split_last(s: str, delimiter: str) -> tuple[str, str]:
    """
    Split string at last occurrence of delimiter.

    Args:
        s: Source string
        delimiter: Delimiter to split on

    Returns:
        Tuple of (before, after), or ("", "") if not found
    """
    if not s or not delimiter:
        return ("", "")
    idx = s.rfind(delimiter)
    if idx == -1:
        return ("", "")
    return (s[:idx], s[idx + len(delimiter):])


# =============================================================================
# Line-based Extraction
# =============================================================================

def line_containing(s: str, substring: str) -> str:
    """
    Get the full line containing a substring.

    Args:
        s: Source string (may contain multiple lines)
        substring: Text to search for

    Returns:
        The complete line containing substring, or "" if not found
    """
    if not s or not substring:
        return ""
    for line in s.splitlines():
        if substring in line:
            return line
    return ""


def lines_containing(s: str, substring: str) -> list[str]:
    """
    Get all lines containing a substring.

    Args:
        s: Source string (may contain multiple lines)
        substring: Text to search for

    Returns:
        List of lines containing substring
    """
    if not s or not substring:
        return []
    return [line for line in s.splitlines() if substring in line]


def lines_between(s: str, start_marker: str, end_marker: str) -> list[str]:
    """
    Get all lines between two markers (exclusive).

    Args:
        s: Source string (may contain multiple lines)
        start_marker: Text marking the start (line containing this is excluded)
        end_marker: Text marking the end (line containing this is excluded)

    Returns:
        List of lines between markers
    """
    if not s or not start_marker or not end_marker:
        return []
    lines = s.splitlines()
    result = []
    capturing = False
    for line in lines:
        if not capturing:
            if start_marker in line:
                capturing = True
        else:
            if end_marker in line:
                break
            result.append(line)
    return result


# =============================================================================
# Context Extraction
# =============================================================================

def around(s: str, match: str, chars_before: int = 50, chars_after: int = 50) -> str:
    """
    Get text surrounding a match with specified context.

    Args:
        s: Source string
        match: Text to find
        chars_before: Number of characters to include before match
        chars_after: Number of characters to include after match

    Returns:
        Text around the match, or "" if not found
    """
    if not s or not match:
        return ""
    idx = s.find(match)
    if idx == -1:
        return ""
    start = max(0, idx - chars_before)
    end = min(len(s), idx + len(match) + chars_after)
    return s[start:end]


# =============================================================================
# Attribute Extraction
# =============================================================================

_ATTR_PATTERN = re.compile(r'([a-zA-Z_][\w-]*)\s*=\s*["\']([^"\']*)["\']')


def attr(s: str, name: str) -> str:
    """
    Extract attribute value from tag-like string.

    Args:
        s: Source string containing attributes (e.g., '<tag name="value">')
        name: Attribute name to extract

    Returns:
        Attribute value, or "" if not found
    """
    if not s or not name:
        return ""
    pattern = re.compile(
        rf'{re.escape(name)}\s*=\s*["\']([^"\']*)["\']',
        re.IGNORECASE
    )
    match = pattern.search(s)
    return match.group(1) if match else ""


def attrs(s: str) -> dict[str, str]:
    """
    Extract all attributes from tag-like string.

    Args:
        s: Source string containing attributes

    Returns:
        Dictionary of attribute name -> value pairs
    """
    if not s:
        return {}
    return dict(_ATTR_PATTERN.findall(s))


# =============================================================================
# Chunk/Slice Utilities
# =============================================================================

def take(s: str, n: int) -> str:
    """
    Take first n characters from string.

    Args:
        s: Source string
        n: Number of characters to take

    Returns:
        First n characters, or full string if shorter
    """
    if not s or n <= 0:
        return ""
    return s[:n]


def take_last(s: str, n: int) -> str:
    """
    Take last n characters from string.

    Args:
        s: Source string
        n: Number of characters to take

    Returns:
        Last n characters, or full string if shorter
    """
    if not s or n <= 0:
        return ""
    return s[-n:] if n < len(s) else s


def skip(s: str, n: int) -> str:
    """
    Skip first n characters from string.

    Args:
        s: Source string
        n: Number of characters to skip

    Returns:
        String with first n characters removed
    """
    if not s:
        return ""
    if n <= 0:
        return s
    return s[n:]


def skip_last(s: str, n: int) -> str:
    """
    Skip last n characters from string.

    Args:
        s: Source string
        n: Number of characters to skip

    Returns:
        String with last n characters removed
    """
    if not s:
        return ""
    if n <= 0:
        return s
    if n >= len(s):
        return ""
    return s[:-n]


def truncate(s: str, max_len: int, suffix: str = "...") -> str:
    """
    Truncate string to max length, adding suffix if truncated.

    Args:
        s: Source string
        max_len: Maximum length (including suffix)
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated string with suffix, or original if within limit
    """
    if not s or max_len <= 0:
        return ""
    if len(s) <= max_len:
        return s
    if len(suffix) >= max_len:
        return suffix[:max_len]
    return s[:max_len - len(suffix)] + suffix


# =============================================================================
# Case Conversion
# =============================================================================

def to_snake_case(s: str) -> str:
    """
    Convert string to snake_case.

    Args:
        s: Input string (camelCase, PascalCase, kebab-case, or spaces)

    Returns:
        snake_case string
    """
    if not s:
        return ""
    # Handle camelCase and PascalCase
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    # Replace spaces, hyphens, and multiple underscores
    result = re.sub(r'[-\s]+', '_', result)
    result = re.sub(r'_+', '_', result)
    return result.lower().strip('_')


def to_camel_case(s: str) -> str:
    """
    Convert string to camelCase.

    Args:
        s: Input string (snake_case, kebab-case, or spaces)

    Returns:
        camelCase string
    """
    if not s:
        return ""
    # Split on underscores, hyphens, spaces
    words = re.split(r'[-_\s]+', s)
    if not words:
        return ""
    # First word lowercase, rest title case
    return words[0].lower() + ''.join(w.title() for w in words[1:])


def to_pascal_case(s: str) -> str:
    """
    Convert string to PascalCase.

    Args:
        s: Input string (snake_case, kebab-case, or spaces)

    Returns:
        PascalCase string
    """
    if not s:
        return ""
    words = re.split(r'[-_\s]+', s)
    return ''.join(w.title() for w in words if w)


def to_kebab_case(s: str) -> str:
    """
    Convert string to kebab-case.

    Args:
        s: Input string (camelCase, PascalCase, snake_case, or spaces)

    Returns:
        kebab-case string
    """
    if not s:
        return ""
    # Handle camelCase and PascalCase
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', s)
    # Replace underscores, spaces, and multiple hyphens
    result = re.sub(r'[_\s]+', '-', result)
    result = re.sub(r'-+', '-', result)
    return result.lower().strip('-')


def to_title_case(s: str) -> str:
    """
    Convert string to Title Case.

    Args:
        s: Input string

    Returns:
        Title Case string with each word capitalized
    """
    if not s:
        return ""
    return ' '.join(word.capitalize() for word in s.split())


# =============================================================================
# String Manipulation
# =============================================================================

def remove(s: str, substring: str) -> str:
    """
    Remove all occurrences of substring.

    Args:
        s: Source string
        substring: Text to remove

    Returns:
        String with all occurrences removed
    """
    if not s or not substring:
        return s or ""
    return s.replace(substring, "")


def replace_first(s: str, old: str, new: str) -> str:
    """
    Replace only the first occurrence of old with new.

    Args:
        s: Source string
        old: Text to find
        new: Replacement text

    Returns:
        String with first occurrence replaced
    """
    if not s or not old:
        return s or ""
    return s.replace(old, new, 1)


def replace_last(s: str, old: str, new: str) -> str:
    """
    Replace only the last occurrence of old with new.

    Args:
        s: Source string
        old: Text to find
        new: Replacement text

    Returns:
        String with last occurrence replaced
    """
    if not s or not old:
        return s or ""
    idx = s.rfind(old)
    if idx == -1:
        return s
    return s[:idx] + new + s[idx + len(old):]


def pad_left(s: str, length: int, char: str = " ") -> str:
    """
    Pad string on the left to reach specified length.

    Args:
        s: Source string
        length: Desired total length
        char: Character to pad with (default: space)

    Returns:
        Left-padded string
    """
    if not s:
        s = ""
    if not char:
        char = " "
    return s.rjust(length, char[0])


def pad_right(s: str, length: int, char: str = " ") -> str:
    """
    Pad string on the right to reach specified length.

    Args:
        s: Source string
        length: Desired total length
        char: Character to pad with (default: space)

    Returns:
        Right-padded string
    """
    if not s:
        s = ""
    if not char:
        char = " "
    return s.ljust(length, char[0])


def reverse(s: str) -> str:
    """
    Reverse a string.

    Args:
        s: Source string

    Returns:
        Reversed string
    """
    if not s:
        return ""
    return s[::-1]


# =============================================================================
# String Queries
# =============================================================================

def count_occurrences(s: str, substring: str) -> int:
    """
    Count occurrences of substring in string.

    Args:
        s: Source string
        substring: Text to count

    Returns:
        Number of occurrences
    """
    if not s or not substring:
        return 0
    return s.count(substring)


def contains_all(s: str, *substrings: str) -> bool:
    """
    Check if string contains all specified substrings.

    Args:
        s: Source string
        *substrings: Substrings to check for

    Returns:
        True if all substrings are present
    """
    if not s or not substrings:
        return False
    return all(sub in s for sub in substrings)


def contains_any(s: str, *substrings: str) -> bool:
    """
    Check if string contains any of the specified substrings.

    Args:
        s: Source string
        *substrings: Substrings to check for

    Returns:
        True if any substring is present
    """
    if not s or not substrings:
        return False
    return any(sub in s for sub in substrings)


def starts_with_any(s: str, *prefixes: str) -> bool:
    """
    Check if string starts with any of the specified prefixes.

    Args:
        s: Source string
        *prefixes: Prefixes to check

    Returns:
        True if string starts with any prefix
    """
    if not s or not prefixes:
        return False
    return any(s.startswith(p) for p in prefixes)


def ends_with_any(s: str, *suffixes: str) -> bool:
    """
    Check if string ends with any of the specified suffixes.

    Args:
        s: Source string
        *suffixes: Suffixes to check

    Returns:
        True if string ends with any suffix
    """
    if not s or not suffixes:
        return False
    return any(s.endswith(sf) for sf in suffixes)


def is_empty(s: str) -> bool:
    """
    Check if string is empty or contains only whitespace.

    Args:
        s: String to check

    Returns:
        True if empty or whitespace only
    """
    if s is None:
        return True
    return len(s.strip()) == 0


def is_numeric(s: str) -> bool:
    """
    Check if string represents a number (int or float).

    Args:
        s: String to check

    Returns:
        True if string is numeric
    """
    if not s or not s.strip():
        return False
    try:
        float(s.strip())
        return True
    except ValueError:
        return False


# =============================================================================
# Word/Sentence Utilities
# =============================================================================

def words(s: str) -> list[str]:
    """
    Split string into words.

    Args:
        s: Source string

    Returns:
        List of words
    """
    if not s:
        return []
    return s.split()


def word_count(s: str) -> int:
    """
    Count number of words in string.

    Args:
        s: Source string

    Returns:
        Number of words
    """
    if not s:
        return 0
    return len(s.split())


def sentences(s: str) -> list[str]:
    """
    Split string into sentences.

    Args:
        s: Source string

    Returns:
        List of sentences
    """
    if not s:
        return []
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', s.strip())
    return [p.strip() for p in parts if p.strip()]


def first_word(s: str) -> str:
    """
    Get the first word from string.

    Args:
        s: Source string

    Returns:
        First word, or "" if empty
    """
    if not s:
        return ""
    parts = s.split()
    return parts[0] if parts else ""


def last_word(s: str) -> str:
    """
    Get the last word from string.

    Args:
        s: Source string

    Returns:
        Last word, or "" if empty
    """
    if not s:
        return ""
    parts = s.split()
    return parts[-1] if parts else ""


def nth_word(s: str, n: int) -> str:
    """
    Get the nth word from string (1-indexed).

    Args:
        s: Source string
        n: Word position (1-indexed)

    Returns:
        Nth word, or "" if not found
    """
    if not s or n < 1:
        return ""
    parts = s.split()
    if n > len(parts):
        return ""
    return parts[n - 1]


# =============================================================================
# Safe Parsing
# =============================================================================

def parse_int(s: str, default: int = 0) -> int:
    """
    Safely parse string to integer.

    Args:
        s: String to parse
        default: Default value if parsing fails

    Returns:
        Parsed integer or default
    """
    if not s:
        return default
    try:
        # Handle floats by truncating
        return int(float(s.strip()))
    except (ValueError, TypeError):
        return default


def parse_float(s: str, default: float = 0.0) -> float:
    """
    Safely parse string to float.

    Args:
        s: String to parse
        default: Default value if parsing fails

    Returns:
        Parsed float or default
    """
    if not s:
        return default
    try:
        return float(s.strip())
    except (ValueError, TypeError):
        return default


def parse_bool(s: str) -> bool:
    """
    Parse string to boolean.

    Recognizes: true/false, yes/no, 1/0, on/off, y/n

    Args:
        s: String to parse

    Returns:
        Boolean value (False for unrecognized values)
    """
    if not s:
        return False
    val = s.strip().lower()
    return val in ('true', 'yes', '1', 'on', 'y', 't')


# =============================================================================
# Slug/Filename Utilities
# =============================================================================

def slugify(s: str, separator: str = "-") -> str:
    """
    Convert string to URL-safe slug.

    Removes special characters, converts spaces to separator,
    and lowercases the result.

    Args:
        s: Source string
        separator: Word separator (default: hyphen)

    Returns:
        URL-safe slug
    """
    if not s:
        return ""
    # Normalize unicode
    slug = unicodedata.normalize("NFKD", s)
    # Remove non-ASCII
    slug = slug.encode("ascii", "ignore").decode("ascii")
    # Convert to lowercase
    slug = slug.lower()
    # Replace spaces and underscores with separator
    slug = re.sub(r'[\s_]+', separator, slug)
    # Remove non-alphanumeric except separator
    slug = re.sub(r'[^a-z0-9' + re.escape(separator) + r']', '', slug)
    # Remove multiple separators
    slug = re.sub(re.escape(separator) + r'+', separator, slug)
    # Strip leading/trailing separators
    return slug.strip(separator)


def to_filename(s: str, replacement: str = "_") -> str:
    """
    Convert string to safe filename.

    Removes/replaces characters not allowed in filenames.

    Args:
        s: Source string
        replacement: Character to replace invalid chars with

    Returns:
        Safe filename
    """
    if not s:
        return ""
    # Characters not allowed in filenames on various OSes
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    result = re.sub(invalid_chars, replacement, s)
    # Remove multiple replacements
    result = re.sub(re.escape(replacement) + r'+', replacement, result)
    # Strip leading/trailing spaces and dots (Windows issues)
    result = result.strip('. ')
    # Limit length (255 is common max for most filesystems)
    return result[:255] if result else ""


# =============================================================================
# String Similarity
# =============================================================================

def common_prefix(s1: str, s2: str) -> str:
    """
    Find the common prefix of two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Common prefix
    """
    if not s1 or not s2:
        return ""
    i = 0
    while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
        i += 1
    return s1[:i]


def common_suffix(s1: str, s2: str) -> str:
    """
    Find the common suffix of two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Common suffix
    """
    if not s1 or not s2:
        return ""
    i = 0
    while i < len(s1) and i < len(s2) and s1[-(i+1)] == s2[-(i+1)]:
        i += 1
    return s1[-i:] if i > 0 else ""


def similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio between two strings.

    Uses a simple character-based comparison.
    Returns value between 0.0 (completely different) and 1.0 (identical).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    # Simple ratio based on common characters
    len1, len2 = len(s1), len(s2)
    max_len = max(len1, len2)

    # Count matching characters at same positions
    matches = sum(1 for i in range(min(len1, len2)) if s1[i] == s2[i])

    # Add bonus for common prefix and suffix
    prefix_len = len(common_prefix(s1, s2))
    suffix_len = len(common_suffix(s1, s2))

    # Calculate ratio
    score = (matches + prefix_len + suffix_len) / (max_len * 2)
    return min(1.0, score)


# =============================================================================
# Text Cleaning
# =============================================================================

def normalize_space(s: str) -> str:
    """Collapse whitespace to single spaces."""
    return " ".join(s.split())


def strip_tags(html_text: str) -> str:
    """Remove HTML tags from text."""
    cleaned = re.sub(r"<[^>]*>", " ", html_text, flags=re.DOTALL)
    return normalize_space(cleaned)


def unescape_html(s: str) -> str:
    """Unescape HTML entities."""
    return html.unescape(s)


def clean_text(text: str) -> str:
    """
    Clean text by normalizing unicode, removing extra whitespace,
    and converting to consistent format.
    """
    if not text:
        return ""
    # Normalize unicode (NFKC normalizes compatibility characters)
    text = unicodedata.normalize("NFKC", text)
    # Replace common unicode whitespace and dashes
    text = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", text)
    text = re.sub(r"[\u2013\u2014\u2212]", "-", text)
    text = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", text)
    text = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', text)
    # Collapse whitespace
    text = " ".join(text.split())
    return text.strip()


# =============================================================================
# Regex Utilities
# =============================================================================

def regex_first(s: str, pattern: str) -> str:
    """Get first regex match (group 1 if exists, else group 0)."""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return ""
    match = compiled.search(s)
    if not match:
        return ""
    if match.groups():
        return match.group(1)
    return match.group(0)


def regex_all(s: str, pattern: str) -> list[str]:
    """Get all regex matches (group 1 if exists, else group 0)."""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return []
    results: list[str] = []
    for m in compiled.finditer(s):
        if m.groups():
            results.append(m.group(1))
        else:
            results.append(m.group(0))
    return results


def parse_csrf_token(html_text: str) -> str:
    """
    Extracts a CSRF token from common hidden input, meta, or inline script patterns.
    Returns empty string when not found.
    """
    patterns = [
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        r'<input[^>]*name=["\']_csrf["\'][^>]*value=["\']([^"\']+)["\']',
        r'<meta[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*name=["\']csrf_token["\'][^>]*content=["\']([^"\']+)["\']',
        r"csrfToken\s*[:=]\s*['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    return ""


# =============================================================================
# URL Encoding
# =============================================================================

def url_encode(params: Mapping[str, Any] | Sequence[tuple[str, Any]]) -> str:
    """URL encode parameters."""
    clean_params: Mapping[str, Any] | Sequence[tuple[str, Any]] = params
    if isinstance(params, Mapping):
        clean_params = {k: "" if v is None else v for k, v in params.items()}
    return urllib.parse.urlencode(clean_params, doseq=True)


def url_decode(query: str) -> dict[str, list[str]]:
    """URL decode query string."""
    return urllib.parse.parse_qs(query, keep_blank_values=True)


# =============================================================================
# Base64 Encoding
# =============================================================================

def b64_encode(data: str | bytes, *, urlsafe: bool = False) -> str:
    """Base64 encode data."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    if urlsafe:
        return base64.urlsafe_b64encode(raw).decode("ascii")
    return base64.b64encode(raw).decode("ascii")


def b64_decode(data: str, *, urlsafe: bool = False) -> bytes:
    """Base64 decode data."""
    if not data:
        return b""
    padded = data + "=" * (-len(data) % 4)
    try:
        if urlsafe:
            return base64.urlsafe_b64decode(padded)
        return base64.b64decode(padded)
    except Exception:
        return b""


# =============================================================================
# Validation
# =============================================================================

_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

_URL_PATTERN = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)


def is_valid_email(text: str) -> bool:
    """Check if text is a valid email address."""
    if not text or not isinstance(text, str):
        return False
    return bool(_EMAIL_PATTERN.match(text.strip()))


def is_valid_url(text: str) -> bool:
    """Check if text is a valid HTTP/HTTPS URL."""
    if not text or not isinstance(text, str):
        return False
    return bool(_URL_PATTERN.match(text.strip()))


def is_valid_json(text: str) -> bool:
    """Check if text is valid JSON."""
    if not text or not isinstance(text, str):
        return False
    try:
        json.loads(text)
        return True
    except Exception:
        return False


# =============================================================================
# Text Extraction
# =============================================================================

_EMAIL_EXTRACT_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

_URL_EXTRACT_PATTERN = re.compile(
    r"https?://[^\s<>\"')\]}>]+", re.IGNORECASE
)

_NUMBER_PATTERN = re.compile(
    r"[$€£¥]?\s*\d+(?:[.,]\d+)*(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD))?|\d+(?:[.,]\d+)*\s*[$€£¥%]?"
)


def extract_emails(text: str) -> list[str]:
    """Extract all email addresses from text."""
    if not text:
        return []
    return list(set(_EMAIL_EXTRACT_PATTERN.findall(text)))


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    if not text:
        return []
    urls = _URL_EXTRACT_PATTERN.findall(text)
    # Clean trailing punctuation
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:!?")
        if url:
            cleaned.append(url)
    return list(set(cleaned))


def extract_numbers(text: str) -> list[str]:
    """Extract all numbers and prices from text."""
    if not text:
        return []
    matches = _NUMBER_PATTERN.findall(text)
    return [m.strip() for m in matches if m.strip()]


# =============================================================================
# Social Media Extraction
# =============================================================================

_DISCORD_INVITE_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([a-zA-Z0-9-]+)",
    re.IGNORECASE,
)

_TELEGRAM_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)",
    re.IGNORECASE,
)

_TWITTER_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_/]+",
    re.IGNORECASE,
)

_YOUTUBE_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s<>\"']+",
    re.IGNORECASE,
)

_INSTAGRAM_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/[a-zA-Z0-9_./-]+",
    re.IGNORECASE,
)

_TIKTOK_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?tiktok\.com/@[a-zA-Z0-9_./-]+",
    re.IGNORECASE,
)

_REDDIT_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?reddit\.com/[ru]/[a-zA-Z0-9_/-]+",
    re.IGNORECASE,
)


def extract_discord_invites(text: str) -> list[str]:
    """Extract Discord invite codes from text."""
    if not text:
        return []
    matches = _DISCORD_INVITE_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_telegram_links(text: str) -> list[str]:
    """Extract Telegram usernames/channels from text."""
    if not text:
        return []
    matches = _TELEGRAM_LINK_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_twitter_links(text: str) -> list[str]:
    """Extract Twitter/X URLs from text."""
    if not text:
        return []
    matches = _TWITTER_LINK_PATTERN.findall(text)
    result = []
    for match in matches:
        url = match if match.startswith("http") else f"https://{match}"
        if url not in result:
            result.append(url)
    return result


def extract_youtube_links(text: str) -> list[str]:
    """Extract YouTube URLs from text."""
    if not text:
        return []
    matches = _YOUTUBE_LINK_PATTERN.findall(text)
    result = []
    for match in matches:
        url = match if match.startswith("http") else f"https://{match}"
        url = url.rstrip(".,;:!?")
        if url not in result:
            result.append(url)
    return result


def extract_instagram_links(text: str) -> list[str]:
    """Extract Instagram URLs from text."""
    if not text:
        return []
    matches = _INSTAGRAM_LINK_PATTERN.findall(text)
    result = []
    for match in matches:
        url = match if match.startswith("http") else f"https://{match}"
        if url not in result:
            result.append(url)
    return result


def extract_tiktok_links(text: str) -> list[str]:
    """Extract TikTok URLs from text."""
    if not text:
        return []
    matches = _TIKTOK_LINK_PATTERN.findall(text)
    result = []
    for match in matches:
        url = match if match.startswith("http") else f"https://{match}"
        if url not in result:
            result.append(url)
    return result


def extract_reddit_links(text: str) -> list[str]:
    """Extract Reddit URLs from text."""
    if not text:
        return []
    matches = _REDDIT_LINK_PATTERN.findall(text)
    result = []
    for match in matches:
        url = match if match.startswith("http") else f"https://{match}"
        if url not in result:
            result.append(url)
    return result


def extract_social_links(text: str) -> dict[str, list[str]]:
    """Extract all social media links from text."""
    return {
        "discord": extract_discord_invites(text),
        "telegram": extract_telegram_links(text),
        "twitter": extract_twitter_links(text),
        "youtube": extract_youtube_links(text),
        "instagram": extract_instagram_links(text),
        "tiktok": extract_tiktok_links(text),
        "reddit": extract_reddit_links(text),
    }


# =============================================================================
# Crypto/Web3 Extraction
# =============================================================================

_ETH_ADDRESS_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

_BTC_LEGACY_PATTERN = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
_BTC_BECH32_PATTERN = re.compile(r"\bbc1[a-z0-9]{39,59}\b")

_SOL_ADDRESS_PATTERN = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

_ENS_NAME_PATTERN = re.compile(r"\b[a-zA-Z0-9][-a-zA-Z0-9]*\.eth\b")


def extract_eth_addresses(text: str) -> list[str]:
    """Extract Ethereum addresses from text."""
    if not text:
        return []
    matches = _ETH_ADDRESS_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_btc_addresses(text: str) -> list[str]:
    """Extract Bitcoin addresses from text."""
    if not text:
        return []
    legacy = _BTC_LEGACY_PATTERN.findall(text)
    bech32 = _BTC_BECH32_PATTERN.findall(text)
    all_matches = legacy + bech32
    return list(dict.fromkeys(all_matches))


def extract_sol_addresses(text: str) -> list[str]:
    """Extract Solana addresses from text."""
    if not text:
        return []
    matches = _SOL_ADDRESS_PATTERN.findall(text)
    # Filter out potential false positives (too short, contains invalid chars)
    valid = []
    for match in matches:
        if len(match) >= 32 and len(match) <= 44:
            # Exclude matches that look like other patterns (ETH, BTC, etc.)
            if not match.startswith("0x") and not match.startswith("bc1"):
                valid.append(match)
    return list(dict.fromkeys(valid))


def extract_ens_names(text: str) -> list[str]:
    """Extract ENS names from text."""
    if not text:
        return []
    matches = _ENS_NAME_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_crypto_addresses(text: str) -> dict[str, list[str]]:
    """Extract all crypto addresses from text."""
    return {
        "eth": extract_eth_addresses(text),
        "btc": extract_btc_addresses(text),
        "sol": extract_sol_addresses(text),
        "ens": extract_ens_names(text),
    }


# =============================================================================
# Security Token Extraction
# =============================================================================

_API_KEY_PATTERNS = [
    ("openai", re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b")),
    ("anthropic", re.compile(r"\bsk-ant-[a-zA-Z0-9-]{20,}\b")),
    ("aws", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
    ("stripe_live", re.compile(r"\bsk_live_[a-zA-Z0-9]{24,}\b")),
    ("stripe_test", re.compile(r"\bsk_test_[a-zA-Z0-9]{24,}\b")),
    ("github", re.compile(r"\bgh[pousr]_[a-zA-Z0-9]{36,}\b")),
    ("google", re.compile(r"\bAIza[a-zA-Z0-9_-]{35}\b")),
    ("discord_bot", re.compile(r"\b[MN][a-zA-Z0-9]{23,}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27,}\b")),
    ("telegram_bot", re.compile(r"\b[0-9]{8,10}:[a-zA-Z0-9_-]{35}\b")),
]

_JWT_PATTERN = re.compile(
    r"\beyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+\b"
)

_BEARER_PATTERN = re.compile(r"\b[Bb]earer\s+([a-zA-Z0-9_.-]+)")


def extract_api_keys(text: str) -> list[dict[str, str]]:
    """Extract API keys from text with type detection."""
    if not text:
        return []
    results = []
    seen = set()
    for key_type, pattern in _API_KEY_PATTERNS:
        for match in pattern.findall(text):
            if match not in seen:
                seen.add(match)
                results.append({"type": key_type, "key": match})
    return results


def extract_jwts(text: str) -> list[str]:
    """Extract JWT tokens from text."""
    if not text:
        return []
    matches = _JWT_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def decode_jwt(token: str) -> dict[str, Any] | None:
    """Decode JWT without verification. Returns header and payload."""
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        # Decode header
        header_b64 = parts[0]
        header_padded = header_b64 + "=" * (-len(header_b64) % 4)
        header_json = base64.urlsafe_b64decode(header_padded).decode("utf-8")
        header = json.loads(header_json)
        # Decode payload
        payload_b64 = parts[1]
        payload_padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_padded).decode("utf-8")
        payload = json.loads(payload_json)
        return {"header": header, "payload": payload}
    except Exception:
        return None


def extract_bearer_tokens(text: str) -> list[str]:
    """Extract Bearer tokens from text."""
    if not text:
        return []
    matches = _BEARER_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


# =============================================================================
# Contact Info Extraction
# =============================================================================

_PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    r"|\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}"
)

_DATE_PATTERNS = [
    # ISO format: 2024-01-15
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    # US format: 01/15/2024 or 01-15-2024
    re.compile(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"),
    # Long format: January 15, 2024
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    ),
    # Short format: 15 Jan 2024
    re.compile(
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b"
    ),
]


def extract_phone_numbers(text: str) -> list[str]:
    """Extract phone numbers from text."""
    if not text:
        return []
    matches = _PHONE_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_dates(text: str) -> list[str]:
    """Extract dates from text in various formats."""
    if not text:
        return []
    results = []
    seen = set()
    for pattern in _DATE_PATTERNS:
        for match in pattern.findall(text):
            if match not in seen:
                seen.add(match)
                results.append(match)
    return results


# =============================================================================
# Network/Identifier Extraction
# =============================================================================

_IPV4_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

_IPV6_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    r'|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b'
    r'|\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b'
    r'|\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b'
)

_DOMAIN_PATTERN = re.compile(
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
)

_UUID_PATTERN = re.compile(
    r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'
)

_MAC_ADDRESS_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b'
)


def extract_ipv4(text: str) -> list[str]:
    """Extract IPv4 addresses from text."""
    if not text:
        return []
    matches = _IPV4_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_ipv6(text: str) -> list[str]:
    """Extract IPv6 addresses from text."""
    if not text:
        return []
    matches = _IPV6_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_ips(text: str) -> list[str]:
    """Extract all IP addresses (IPv4 and IPv6) from text."""
    if not text:
        return []
    ipv4 = extract_ipv4(text)
    ipv6 = extract_ipv6(text)
    return ipv4 + ipv6


def extract_domains(text: str) -> list[str]:
    """Extract domain names from text."""
    if not text:
        return []
    matches = _DOMAIN_PATTERN.findall(text)
    # Filter out common false positives
    filtered = []
    for domain in matches:
        lower = domain.lower()
        # Skip file extensions that look like domains
        if not any(lower.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.gif', '.svg']):
            if domain not in filtered:
                filtered.append(domain)
    return filtered


def extract_uuids(text: str) -> list[str]:
    """Extract UUIDs from text."""
    if not text:
        return []
    matches = _UUID_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


def extract_mac_addresses(text: str) -> list[str]:
    """Extract MAC addresses from text."""
    if not text:
        return []
    matches = _MAC_ADDRESS_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


# =============================================================================
# API/Endpoint Extraction
# =============================================================================

_API_ENDPOINT_PATTERN = re.compile(
    r'["\'](?:https?://[^"\']*)?(/(?:api|v\d+|graphql|rest)/[^"\']*)["\']',
    re.IGNORECASE,
)

_GRAPHQL_ENDPOINT_PATTERN = re.compile(
    r'["\']([^"\']*(?:graphql|gql)[^"\']*)["\']',
    re.IGNORECASE,
)

_WEBSOCKET_URL_PATTERN = re.compile(
    r'["\']?(wss?://[^\s"\'<>]+)["\']?',
    re.IGNORECASE,
)

_FULL_API_URL_PATTERN = re.compile(
    r'https?://[^\s"\'<>]*(?:/api/|/v\d+/|/rest/)[^\s"\'<>]*',
    re.IGNORECASE,
)


def extract_api_endpoints(text: str) -> list[str]:
    """Extract API endpoint paths from text."""
    if not text:
        return []
    # Get relative paths
    paths = _API_ENDPOINT_PATTERN.findall(text)
    # Get full URLs
    urls = _FULL_API_URL_PATTERN.findall(text)
    all_endpoints = paths + urls
    return list(dict.fromkeys(all_endpoints))


def extract_graphql_endpoints(text: str) -> list[str]:
    """Extract GraphQL endpoint URLs from text."""
    if not text:
        return []
    matches = _GRAPHQL_ENDPOINT_PATTERN.findall(text)
    # Filter to likely endpoints
    endpoints = []
    for match in matches:
        if '/' in match or match.endswith('graphql') or match.endswith('gql'):
            if match not in endpoints:
                endpoints.append(match)
    return endpoints


def extract_websocket_urls(text: str) -> list[str]:
    """Extract WebSocket URLs from text."""
    if not text:
        return []
    matches = _WEBSOCKET_URL_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


# =============================================================================
# Media URL Extraction
# =============================================================================

_VIDEO_URL_PATTERN = re.compile(
    r'["\']?(https?://[^\s"\'<>]+\.(?:mp4|webm|m3u8|mpd|avi|mov|mkv|flv|wmv)(?:\?[^\s"\'<>]*)?)["\']?',
    re.IGNORECASE,
)

_VIDEO_SRC_PATTERN = re.compile(
    r'<(?:video|source)[^>]*src=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_AUDIO_URL_PATTERN = re.compile(
    r'["\']?(https?://[^\s"\'<>]+\.(?:mp3|wav|ogg|m4a|flac|aac|wma)(?:\?[^\s"\'<>]*)?)["\']?',
    re.IGNORECASE,
)

_AUDIO_SRC_PATTERN = re.compile(
    r'<(?:audio|source)[^>]*src=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_STREAM_URL_PATTERN = re.compile(
    r'["\']?(https?://[^\s"\'<>]*(?:\.m3u8|\.mpd|/manifest|/playlist)[^\s"\'<>]*)["\']?',
    re.IGNORECASE,
)


def extract_video_urls(text: str) -> list[str]:
    """Extract video URLs from text/HTML."""
    if not text:
        return []
    # Direct URLs
    urls = _VIDEO_URL_PATTERN.findall(text)
    # From video/source tags
    src_urls = _VIDEO_SRC_PATTERN.findall(text)
    # Streaming URLs
    stream_urls = _STREAM_URL_PATTERN.findall(text)
    all_urls = urls + src_urls + stream_urls
    return list(dict.fromkeys(all_urls))


def extract_audio_urls(text: str) -> list[str]:
    """Extract audio URLs from text/HTML."""
    if not text:
        return []
    # Direct URLs
    urls = _AUDIO_URL_PATTERN.findall(text)
    # From audio/source tags
    src_urls = _AUDIO_SRC_PATTERN.findall(text)
    all_urls = urls + src_urls
    return list(dict.fromkeys(all_urls))


def extract_stream_urls(text: str) -> list[str]:
    """Extract streaming URLs (m3u8, mpd) from text."""
    if not text:
        return []
    matches = _STREAM_URL_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


# =============================================================================
# E-commerce/Price Extraction
# =============================================================================

_PRICE_PATTERN = re.compile(
    r'(?:[$\u20ac\u00a3\u00a5]|USD|EUR|GBP|JPY|CAD|AUD)\s*[\d,]+(?:\.\d{2})?'
    r'|[\d,]+(?:\.\d{2})?\s*(?:[$\u20ac\u00a3\u00a5]|USD|EUR|GBP|JPY|CAD|AUD)'
    r'|\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?=\s*(?:dollars?|euros?|pounds?))',
    re.IGNORECASE,
)

_SKU_PATTERN = re.compile(
    r'(?:sku|item|product|part)[\s:_-]*#?\s*([A-Z0-9][-A-Z0-9]{3,20})',
    re.IGNORECASE,
)

_CURRENCY_MAP = {
    '$': 'USD', '\u20ac': 'EUR', '\u00a3': 'GBP', '\u00a5': 'JPY',
    'USD': 'USD', 'EUR': 'EUR', 'GBP': 'GBP', 'JPY': 'JPY',
    'CAD': 'CAD', 'AUD': 'AUD',
}


def extract_prices(text: str) -> list[dict[str, Any]]:
    """Extract prices with currency from text."""
    if not text:
        return []
    matches = _PRICE_PATTERN.findall(text)
    results = []
    seen = set()
    for match in matches:
        if match in seen:
            continue
        seen.add(match)
        # Detect currency
        currency = 'USD'
        for symbol, curr in _CURRENCY_MAP.items():
            if symbol in match:
                currency = curr
                break
        # Extract numeric value
        nums = re.findall(r'[\d,]+(?:\.\d{2})?', match)
        if nums:
            value = nums[0].replace(',', '')
            results.append({
                'raw': match.strip(),
                'value': float(value) if '.' in value else int(value),
                'currency': currency,
            })
    return results


def extract_skus(text: str) -> list[str]:
    """Extract product SKUs from text."""
    if not text:
        return []
    matches = _SKU_PATTERN.findall(text)
    return list(dict.fromkeys(matches))


# =============================================================================
# Structured Data Extraction
# =============================================================================

_CANONICAL_URL_PATTERN = re.compile(
    r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_OG_TAG_PATTERN = re.compile(
    r'<meta[^>]*property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']*)["\']'
    r'|<meta[^>]*content=["\']([^"\']*)["\'][^>]*property=["\']og:([^"\']+)["\']',
    re.IGNORECASE,
)

_TWITTER_CARD_PATTERN = re.compile(
    r'<meta[^>]*name=["\']twitter:([^"\']+)["\'][^>]*content=["\']([^"\']*)["\']'
    r'|<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']twitter:([^"\']+)["\']',
    re.IGNORECASE,
)

_SCHEMA_ORG_PATTERN = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def extract_canonical_url(html: str) -> str:
    """Extract canonical URL from HTML."""
    if not html:
        return ""
    match = _CANONICAL_URL_PATTERN.search(html)
    return match.group(1) if match else ""


def extract_og_tags(html: str) -> dict[str, str]:
    """Extract Open Graph meta tags from HTML."""
    if not html:
        return {}
    tags = {}
    for match in _OG_TAG_PATTERN.finditer(html):
        if match.group(1) and match.group(2):
            tags[match.group(1)] = match.group(2)
        elif match.group(3) and match.group(4):
            tags[match.group(4)] = match.group(3)
    return tags


def extract_twitter_cards(html: str) -> dict[str, str]:
    """Extract Twitter Card meta tags from HTML."""
    if not html:
        return {}
    cards = {}
    for match in _TWITTER_CARD_PATTERN.finditer(html):
        if match.group(1) and match.group(2):
            cards[match.group(1)] = match.group(2)
        elif match.group(3) and match.group(4):
            cards[match.group(4)] = match.group(3)
    return cards


def extract_schema_org(html: str) -> list[Any]:
    """Extract Schema.org JSON-LD data from HTML."""
    if not html:
        return []
    results = []
    for match in _SCHEMA_ORG_PATTERN.finditer(html):
        try:
            data = json.loads(match.group(1))
            results.append(data)
        except (json.JSONDecodeError, ValueError):
            continue
    return results


def extract_structured_data(html: str) -> dict[str, Any]:
    """Extract all structured data (OG, Twitter, Schema.org, canonical)."""
    return {
        'canonical': extract_canonical_url(html),
        'og': extract_og_tags(html),
        'twitter': extract_twitter_cards(html),
        'schema_org': extract_schema_org(html),
    }


__all__ = [
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
    "clean_text",
    # Regex
    "regex_first",
    "regex_all",
    "parse_csrf_token",
    # URL encoding
    "url_encode",
    "url_decode",
    # Base64
    "b64_encode",
    "b64_decode",
    # Validation
    "is_valid_email",
    "is_valid_url",
    "is_valid_json",
    # Text extraction
    "extract_emails",
    "extract_urls",
    "extract_numbers",
    # Social media
    "extract_discord_invites",
    "extract_telegram_links",
    "extract_twitter_links",
    "extract_youtube_links",
    "extract_instagram_links",
    "extract_tiktok_links",
    "extract_reddit_links",
    "extract_social_links",
    # Crypto
    "extract_eth_addresses",
    "extract_btc_addresses",
    "extract_sol_addresses",
    "extract_ens_names",
    "extract_crypto_addresses",
    # Security tokens
    "extract_api_keys",
    "extract_jwts",
    "decode_jwt",
    "extract_bearer_tokens",
    # Contact info
    "extract_phone_numbers",
    "extract_dates",
    # Network/identifiers
    "extract_ipv4",
    "extract_ipv6",
    "extract_ips",
    "extract_domains",
    "extract_uuids",
    "extract_mac_addresses",
    # API endpoints
    "extract_api_endpoints",
    "extract_graphql_endpoints",
    "extract_websocket_urls",
    # Media URLs
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
]
