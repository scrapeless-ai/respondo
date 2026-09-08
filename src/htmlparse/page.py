"""Semantic page extraction using only the standard library's HTML parser."""

from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlsplit


_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_SKIP = {"head", "title", "script", "style", "template", "noscript"}
_HEAD_ELEMENTS = {"head", "base", "link", "meta", "title", "style", "script", "noscript", "template"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_BLOCKS = _HEADINGS | {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",
    "dt", "footer", "header", "hr", "li", "main", "nav", "ol", "p", "pre",
    "section", "table", "td", "th", "tr", "ul",
}


class _PageParser(HTMLParser):
    def __init__(self, base: Optional[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.headings: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        self.text_parts: List[str] = []
        self._skipped: List[str] = []
        self._elements: List[str] = []
        self._heading_depth = 0
        self._link_depth = 0
        self._heading: Optional[Dict[str, Any]] = None
        self._heading_parts: List[str] = []
        self._link: Optional[Dict[str, Any]] = None
        self._link_parts: List[str] = []

    def _finish_heading(self) -> None:
        if self._heading is not None:
            self._heading["text"] = " ".join("".join(self._heading_parts).split())
            self.headings.append(self._heading)
            self._heading = None
            self._heading_parts = []

    def _finish_link(self) -> None:
        if self._link is not None:
            self._link["text"] = " ".join("".join(self._link_parts).split())
            self.links.append(self._link)
            self._link = None
            self._link_parts = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if self._skipped == ["head"] and tag not in _HEAD_ELEMENTS:
            self._skipped.clear()  # HTML permits an omitted </head>.
        if tag in _SKIP:
            self._skipped.append(tag)
        if self._skipped:
            return
        attributes = {key: value or "" for key, value in attrs}
        if tag in _BLOCKS:
            self.handle_data(" ")
        if tag in _HEADINGS:
            self._finish_heading()
            self._heading = {"level": int(tag[1]), "id": attributes.get("id", "")}
            self._heading_depth = len(self._elements)
        if tag == "a":
            self._finish_link()
            self._link_depth = len(self._elements)
            href = attributes.get("href", "").strip()
            try:
                resolved = urljoin(self.base, href) if self.base else href
                scheme = urlsplit(resolved).scheme.lower()
            except ValueError:
                resolved, scheme = "", "invalid"
            # Return navigational links only; never turn script/data URLs into links.
            if href and scheme in {"", "http", "https", "mailto", "tel"}:
                self._link = {
                    "href": resolved,
                    "title": attributes.get("title", ""),
                    "rel": attributes.get("rel", "").lower().split(),
                }
        elif tag == "img" and self._link is not None:
            self._link_parts.append(attributes.get("alt", ""))
        if tag not in _VOID:
            self._elements.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._skipped:
            if tag in self._skipped:
                # Recover from an unclosed nested skip element at its parent's end.
                index = len(self._skipped) - 1 - self._skipped[::-1].index(tag)
                del self._skipped[index:]
            return
        if tag in self._elements:
            depth = len(self._elements) - 1 - self._elements[::-1].index(tag)
            if self._heading is not None and self._heading_depth >= depth:
                self._finish_heading()
            if self._link is not None and self._link_depth >= depth:
                self._finish_link()
            del self._elements[depth:]
        if tag in _BLOCKS:
            self.handle_data(" ")

    def handle_data(self, data: str) -> None:
        if self._skipped:
            return
        self.text_parts.append(data)
        if self._heading is not None:
            self._heading_parts.append(data)
        if self._link is not None:
            self._link_parts.append(data)

    def close(self) -> None:
        super().close()
        self._finish_heading()
        self._finish_link()


def _parse_page(html_text: str, base: Optional[str] = None) -> _PageParser:
    parser = _PageParser(base)
    parser.feed(html_text)
    parser.close()
    return parser


def extract_headings(html_text: str) -> List[Dict[str, Any]]:
    """Return h1–h6 entries as ``{level, id, text}`` in document order.

    Inline markup is preserved as text; head, scripts, styles, templates and
    noscript content are excluded. No CSS is evaluated. Unclosed headings are
    retained at end of input.
    """
    return _parse_page(html_text).headings


def extract_link_details(
    html_text: str, base: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return anchor ``href``, ``text``, ``title`` and ``rel`` attributes.

    Resolve relative URLs against the supplied base (HTML base tags are ignored).
    Allow HTTP(S), mailto, tel and relative links; skip other schemes and empty
    hrefs. Duplicates are preserved in document order, and image alt text is
    included in the link label. This is extraction, not HTML sanitization.
    """
    return _parse_page(html_text, base).links


def extract_page(html_text: str, base: Optional[str] = None) -> Dict[str, Any]:
    """Extract text, metadata, headings, links, images and tables in one call.

    Returns a JSON-serializable dict with a stable shape even for empty input.
    Text uses semantic block spacing and excludes non-content elements; this
    parser does not execute JavaScript or evaluate CSS visibility.
    """
    from htmlparse import extract_images, extract_meta, extract_tables

    parser = _parse_page(html_text, base)
    meta = extract_meta(html_text)
    return {
        "title": meta.get("title", ""),
        "text": " ".join("".join(parser.text_parts).split()),
        "meta": meta,
        "headings": parser.headings,
        "links": parser.links,
        "images": extract_images(html_text, base),
        "tables": extract_tables(html_text),
    }
