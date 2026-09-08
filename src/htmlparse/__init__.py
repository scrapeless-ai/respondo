"""
HTML Parsing and Extraction Module

Provides HTML parsing, text extraction, form/table parsing, and HTML-to-Markdown conversion.
No external dependencies - uses stdlib only (html.parser, re, json, urllib.parse).
"""

import json
import re
from html import unescape as html_unescape
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from .page import extract_headings, extract_link_details, extract_page


def strip_scripts_styles(html_text: str) -> str:
    """
    Remove script and style tags from HTML, returning clean text.

    Args:
        html_text: HTML content

    Returns:
        Text content with scripts, styles, and tags removed
    """
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(html_unescape(text).split())


def get_text(html_text: str, separator: str = " ", strip: bool = True) -> str:
    """
    Extract visible text from HTML.

    Args:
        html_text: HTML content
        separator: Text separator (default: space)
        strip: Whether to strip whitespace

    Returns:
        Extracted text content
    """
    cleaned = strip_scripts_styles(html_text)
    if not separator:
        return cleaned
    parts = cleaned.split()
    return separator.join(parts) if strip else separator.join(cleaned.split(separator))


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attr_map = {k.lower(): v for k, v in attrs}
        href = attr_map.get("href")
        src = attr_map.get("src")
        if href:
            self.links.append(href)
        if src:
            self.links.append(src)


def extract_links(
    html_text: str,
    base: Optional[str] = None,
    same_host: bool = False,
    extensions: Optional[List[str]] = None
) -> List[str]:
    """
    Extract all links (href and src) from HTML.

    Args:
        html_text: HTML content
        base: Base URL for resolving relative links
        same_host: Only include links from same host
        extensions: Filter by file extensions

    Returns:
        List of extracted URLs
    """
    parser = _LinkParser()
    parser.feed(html_text)
    urls = parser.links
    resolved: List[str] = []
    for u in urls:
        full = urljoin(base, u) if base else u
        if same_host and base:
            if urlparse(full).netloc != urlparse(base).netloc:
                continue
        if extensions:
            if not any(full.lower().endswith(ext.lower()) for ext in extensions):
                continue
        resolved.append(full)
    return resolved


class _FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: List[Dict[str, Any]] = []
        self._current_form: Optional[Dict[str, Any]] = None
        self._current_textarea: Optional[str] = None
        self._textarea_buffer: List[str] = []
        self._in_select: Optional[str] = None
        self._select_options: List[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attr_map = {k.lower(): v for k, v in attrs}
        if tag.lower() == "form":
            self._current_form = {
                "action": attr_map.get("action", ""),
                "method": (attr_map.get("method") or "get").lower(),
                "fields": {},
            }
        elif self._current_form and tag.lower() == "input":
            name = attr_map.get("name")
            if not name:
                return
            input_type = (attr_map.get("type") or "text").lower()
            value = attr_map.get("value") or ""
            if input_type in {"checkbox", "radio"} and "checked" not in attr_map:
                return
            self._current_form["fields"][name] = value
        elif self._current_form and tag.lower() == "textarea":
            self._current_textarea = attr_map.get("name")
            self._textarea_buffer = []
        elif self._current_form and tag.lower() == "select":
            self._in_select = attr_map.get("name")
            self._select_options = []
        elif self._current_form and tag.lower() == "option" and self._in_select:
            val = attr_map.get("value") or ""
            selected = "selected" in attr_map
            self._select_options.append((val, selected))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None
        elif tag.lower() == "textarea" and self._current_form is not None and self._current_textarea:
            self._current_form["fields"][self._current_textarea] = "".join(self._textarea_buffer).strip()
            self._current_textarea = None
            self._textarea_buffer = []
        elif tag.lower() == "select" and self._current_form is not None and self._in_select:
            value = ""
            for v, selected in self._select_options:
                if selected:
                    value = v
                    break
            if not value and self._select_options:
                value = self._select_options[0][0]
            self._current_form["fields"][self._in_select] = value
            self._in_select = None
            self._select_options = []

    def handle_data(self, data: str) -> None:
        if self._current_textarea is not None:
            self._textarea_buffer.append(data)


def extract_forms(html_text: str, base: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract all forms with their fields from HTML.

    Args:
        html_text: HTML content
        base: Base URL for resolving action URLs

    Returns:
        List of form dicts with 'action', 'method', 'fields'
    """
    parser = _FormParser()
    parser.feed(html_text)
    forms = parser.forms
    if base:
        forms = [
            {**f, "action": urljoin(base, f.get("action", ""))}
            for f in forms
        ]
    return forms


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: List[List[List[str]]] = []
        self._current_table: Optional[List[List[str]]] = None
        self._current_row: Optional[List[str]] = None
        self._capture_cell: bool = False
        self._cell_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "table":
            self._current_table = []
        elif tag.lower() == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag.lower() in {"td", "th"} and self._current_row is not None:
            self._capture_cell = True
            self._cell_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._capture_cell and self._current_row is not None:
            self._capture_cell = False
            text = "".join(self._cell_buffer).strip()
            self._current_row.append(" ".join(text.split()))
        elif tag.lower() == "tr" and self._current_table is not None and self._current_row is not None:
            self._current_table.append(self._current_row)
            self._current_row = None
        elif tag.lower() == "table" and self._current_table is not None:
            self.tables.append(self._current_table)
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._capture_cell:
            self._cell_buffer.append(data)


def extract_tables(html_text: str) -> List[Dict[str, Any]]:
    """
    Extract tables from HTML as structured data.

    Args:
        html_text: HTML content

    Returns:
        List of table dicts with 'headers' and 'rows'
    """
    parser = _TableParser()
    parser.feed(html_text)
    result: List[Dict[str, Any]] = []
    for table in parser.tables:
        if not table:
            continue
        headers: List[str] = []
        rows_data = table
        if table and len(table[0]) > 0:
            headers = table[0]
            rows_data = table[1:]
        rows: List[Any] = []
        if headers:
            for row in rows_data:
                row_dict = {}
                for idx, header in enumerate(headers):
                    row_dict[header] = row[idx] if idx < len(row) else ""
                rows.append(row_dict)
        else:
            rows = rows_data
        result.append({"headers": headers, "rows": rows})
    return result


def json_in_html(html_text: str) -> List[Any]:
    """
    Extract JSON objects embedded in HTML (script tags and inline assignments).

    Args:
        html_text: HTML content

    Returns:
        List of parsed JSON objects
    """
    results: List[Any] = []
    script_json = re.findall(
        r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    inline_json = re.findall(
        r"(?:var|let|const)\s+[A-Za-z0-9_]+\s*=\s*({.*?});",
        html_text,
        flags=re.DOTALL,
    )
    for chunk in script_json + inline_json:
        try:
            results.append(json.loads(chunk))
        except Exception:
            continue
    return results


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: Dict[str, str] = {}
        self.title: str = ""
        self._in_title: bool = False
        self._title_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attr_map = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "title":
            self._in_title = True
            self._title_buffer = []
        elif tag.lower() == "meta":
            name = attr_map.get("name", "") or attr_map.get("property", "")
            content = attr_map.get("content", "")
            if name and content:
                self.meta[name.lower()] = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_buffer).strip()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buffer.append(data)


def extract_meta(html_text: str) -> Dict[str, str]:
    """
    Extract meta tags from HTML.

    Args:
        html_text: HTML content

    Returns:
        Dict with title, description, og:*, twitter:*, etc.
    """
    parser = _MetaParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass
    result: Dict[str, str] = {}
    if parser.title:
        result["title"] = parser.title
    for key in ["description", "keywords", "author", "viewport", "robots"]:
        if key in parser.meta:
            result[key] = parser.meta[key]
    for key, val in parser.meta.items():
        if key.startswith("og:") or key.startswith("twitter:"):
            result[key] = val
    return result


class _ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: List[Dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "img":
            attr_map = {k.lower(): v or "" for k, v in attrs}
            src = attr_map.get("src", "")
            if src:
                self.images.append({
                    "src": src,
                    "alt": attr_map.get("alt", ""),
                    "title": attr_map.get("title", ""),
                    "width": attr_map.get("width", ""),
                    "height": attr_map.get("height", ""),
                })


def extract_images(html_text: str, base: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extract all images from HTML with their attributes.

    Args:
        html_text: HTML content
        base: Base URL for resolving relative src

    Returns:
        List of image dicts with src, alt, title, width, height
    """
    parser = _ImageParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass
    images = parser.images
    if base:
        for img in images:
            img["src"] = urljoin(base, img["src"])
    return images


class _MarkdownConverter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.output: List[str] = []
        self._list_stack: List[str] = []
        self._link_href: str = ""
        self._in_pre: bool = False
        self._skip: bool = False

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        attr_map = {k.lower(): v or "" for k, v in attrs}

        if tag in ("script", "style"):
            self._skip = True
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.output.append("\n" + "#" * level + " ")
        elif tag == "p":
            self.output.append("\n\n")
        elif tag == "br":
            self.output.append("\n")
        elif tag == "hr":
            self.output.append("\n\n---\n\n")
        elif tag in ("strong", "b"):
            self.output.append("**")
        elif tag in ("em", "i"):
            self.output.append("*")
        elif tag == "code" and not self._in_pre:
            self.output.append("`")
        elif tag == "pre":
            self._in_pre = True
            self.output.append("\n```\n")
        elif tag == "a":
            self._link_href = attr_map.get("href", "")
            self.output.append("[")
        elif tag == "img":
            src = attr_map.get("src", "")
            alt = attr_map.get("alt", "")
            self.output.append(f"![{alt}]({src})")
        elif tag == "ul":
            self._list_stack.append("ul")
            self.output.append("\n")
        elif tag == "ol":
            self._list_stack.append("ol")
            self.output.append("\n")
        elif tag == "li":
            indent = "  " * (len(self._list_stack) - 1)
            if self._list_stack and self._list_stack[-1] == "ol":
                self.output.append(f"{indent}1. ")
            else:
                self.output.append(f"{indent}- ")
        elif tag == "blockquote":
            self.output.append("\n> ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in ("script", "style"):
            self._skip = False
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.append("\n")
        elif tag == "p":
            self.output.append("\n")
        elif tag in ("strong", "b"):
            self.output.append("**")
        elif tag in ("em", "i"):
            self.output.append("*")
        elif tag == "code" and not self._in_pre:
            self.output.append("`")
        elif tag == "pre":
            self._in_pre = False
            self.output.append("\n```\n")
        elif tag == "a":
            self.output.append(f"]({self._link_href})")
            self._link_href = ""
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self.output.append("\n")
        elif tag == "li":
            self.output.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_pre:
            self.output.append(data)
        else:
            text = " ".join(data.split())
            if text:
                self.output.append(text)


def html_to_markdown(html_text: str) -> str:
    """
    Convert HTML to Markdown.

    Supports headings, paragraphs, links, images, lists, bold, italic, code, blockquotes.

    Args:
        html_text: HTML content

    Returns:
        Markdown string
    """
    if not html_text:
        return ""
    converter = _MarkdownConverter()
    try:
        converter.feed(html_text)
    except Exception:
        pass
    result = "".join(converter.output)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


from .selectors import select_html, extract_records


__all__ = [
    "select_html", "extract_records",
    "strip_scripts_styles",
    "get_text",
    "extract_links",
    "extract_forms",
    "extract_tables",
    "json_in_html",
    "extract_meta",
    "extract_images",
    "html_to_markdown",
    "extract_headings",
    "extract_link_details",
    "extract_page",
]
