"""Local RSS 2.0, Atom and sitemap extraction with bounded, DTD-free XML parsing."""

import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin


_ATOM = "http://www.w3.org/2005/Atom"
_SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
_XML = "http://www.w3.org/XML/1998/namespace"
_CONTENT = "http://purl.org/rss/1.0/modules/content/"
_DC = "http://purl.org/dc/elements/1.1/"
_MAX_BYTES = 10 * 1024 * 1024


class _NoDTD(ET.TreeBuilder):
    def __init__(self):
        super().__init__()
        self.depth = 0

    def start(self, tag, attrs):
        self.depth += 1
        if self.depth > 128:
            raise ValueError("XML depth limit of 128 exceeded")
        return super().start(tag, attrs)

    def end(self, tag):
        result = super().end(tag)
        self.depth -= 1
        return result

    def doctype(self, name, pubid, system):
        raise ValueError("DTD declarations are not allowed")


def _parse(xml: Union[str, bytes], max_bytes: int):
    if not isinstance(xml, (str, bytes)):
        raise TypeError("XML input must be a string or bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise ValueError("XML byte limit must be a positive integer")
    if len(xml) > max_bytes or (isinstance(xml, str) and len(xml.encode("utf-8")) > max_bytes):
        raise ValueError("XML input exceeds the byte limit")
    try:
        return ET.fromstring(xml, parser=ET.XMLParser(target=_NoDTD()))
    except ET.ParseError as exc:
        line, column = exc.position
        raise ValueError(f"invalid XML at line {line}, column {column}") from None
    except (LookupError, UnicodeError):
        raise ValueError("unsupported or invalid XML encoding") from None


def _namespace(node) -> str:
    return node.tag[1:].split("}", 1)[0] if node.tag.startswith("{") else ""


def _tag(namespace: str, name: str) -> str:
    return "{" + namespace + "}" + name if namespace else name


def _children(node, name: str):
    return node.findall(_tag(_namespace(node), name))


def _child(node, name: str):
    return node.find(_tag(_namespace(node), name))


def _value(node) -> str:
    if node is None:
        return ""
    # Keep embedded XHTML serialized, and escaped HTML/CDATA as text.
    return ((node.text or "") + "".join(ET.tostring(child, encoding="unicode") for child in node)).strip()


def _field(node, name: str) -> str:
    return _value(_child(node, name))


def _bases(root, base: Optional[str]) -> dict:
    if base is not None and not isinstance(base, str):
        raise TypeError("base must be a string or None")
    values = {}
    total = 0
    pending = [(root, base or "")]
    while pending:
        node, inherited = pending.pop()
        try:
            resolved = urljoin(inherited, node.get(_tag(_XML, "base"), ""))
        except ValueError:
            raise ValueError("invalid XML base URL") from None
        total += len(resolved)
        if len(resolved) > 8192 or total > 8 * 1024 * 1024:
            raise ValueError("XML resolved-base size limit exceeded")
        values[node] = resolved
        pending.extend((child, values[node]) for child in node)
    return values


def _url(value: str, node, bases: dict) -> str:
    try:
        return urljoin(bases.get(node, ""), value) if value else ""
    except ValueError:
        raise ValueError("invalid extracted URL or base") from None


def parse_sitemap(xml: Union[str, bytes], base: Optional[str] = None, *, max_bytes: int = _MAX_BYTES) -> Dict[str, Any]:
    """Extract {type, entries} from a URL set or sitemap index, without fetching.

    Accepts the sitemap namespace or unqualified XML. Entries retain document
    order and string metadata: loc/lastmod, plus changefreq/priority for URL sets.
    Missing loc raises ValueError; unknown extension elements are ignored. This
    extracts data, not full sitemap-schema validation. Relative locations resolve
    using explicit base and inherited xml:base; extracted URLs are not sanitized.
    DTDs are rejected at parser level (including UTF-16); input defaults to 10 MiB
    maximum. XML depth is limited to 128; resolved bases to 8192 characters each
    and 8,388,608 characters cumulative. Keep Python/Expat patched for untrusted documents.
    """
    root = _parse(xml, max_bytes)
    namespace = _namespace(root)
    kind = root.tag.split("}")[-1]
    if namespace not in {"", _SITEMAP} or kind not in {"urlset", "sitemapindex"}:
        raise ValueError("expected a sitemap urlset or sitemapindex root")
    bases = _bases(root, base)
    result = []
    fields = ["loc", "lastmod"] + (["changefreq", "priority"] if kind == "urlset" else [])
    for node in _children(root, "url" if kind == "urlset" else "sitemap"):
        record = {name: _field(node, name) for name in fields}
        if not record["loc"]:
            raise ValueError("sitemap entry requires a nonempty loc")
        record["loc"] = _url(record["loc"], _child(node, "loc"), bases)
        result.append(record)
    return {"type": kind, "entries": result}


def _atom_authors(node) -> list:
    return [name for author in _children(node, "author")
            for name in [_field(author, "name") or _field(author, "email")] if name]


def _atom_link(node, bases: dict) -> str:
    for link in _children(node, "link"):
        if link.get("rel", "alternate") == "alternate" and link.get("href"):
            return _url(link.get("href"), link, bases)
    return ""


def _enclosures(node, bases: dict, atom: bool) -> list:
    result = []
    for link in _children(node, "link" if atom else "enclosure"):
        if atom and link.get("rel") != "enclosure":
            continue
        url = link.get("href" if atom else "url", "")
        if url:
            result.append({"url": _url(url, link, bases), "type": link.get("type", ""), "length": link.get("length", "")})
    return result


def _rss_entry(node, bases: dict) -> dict:
    link_node = _child(node, "link")
    link = _field(node, "link")
    guid = _child(node, "guid")
    if not link and guid is not None and guid.get("isPermaLink", "true").lower() == "true":
        candidate = _value(guid)
        if candidate.startswith(("http://", "https://")):
            link, link_node = candidate, guid
    return {
        "id": _field(node, "guid"), "title": _field(node, "title"),
        "link": _url(link, link_node, bases), "summary": _field(node, "description"),
        "content": _value(node.find(_tag(_CONTENT, "encoded"))),
        "published": _field(node, "pubDate") or _value(node.find(_tag(_DC, "date"))), "updated": "",
        "authors": [_value(author) for author in _children(node, "author") + node.findall(_tag(_DC, "creator")) if _value(author)],
        "categories": [_value(category) for category in _children(node, "category")],
        "enclosures": _enclosures(node, bases, False),
    }


def parse_feed(xml: Union[str, bytes], base: Optional[str] = None, *, max_bytes: int = _MAX_BYTES) -> Dict[str, Any]:
    """Normalize local RSS 2.0 or Atom into feed metadata and ordered entries.

    Returns format/title/link/description/language/entries. Entry fields are
    id/title/link/summary/content/published/updated/authors/categories/enclosures;
    absent scalars are empty strings and absent collections are empty lists.
    Dates remain source strings. HTML content remains untrusted markup (not
    sanitized); XHTML is reserialized with ElementTree namespace prefixes.
    Atom chooses the first alternate link and inherits feed authors if absent.
    URL resolution honors base and xml:base, never fetches or follows anything.
    Supports standard Atom namespace or unqualified feed, and unqualified RSS.
    Rejects DTDs, XML deeper than 128 elements, bases over 8192 characters or 8,388,608 characters
    cumulative, and inputs over max_bytes (default 10 MiB); not an XML schema
    validator. Keep the host Python/Expat security updates current.
    """
    root = _parse(xml, max_bytes)
    bases = _bases(root, base)
    if root.tag == "rss":
        channel = _child(root, "channel")
        if channel is None:
            raise ValueError("RSS requires a channel element")
        return {"format": "rss", "title": _field(channel, "title"),
                "link": _url(_field(channel, "link"), _child(channel, "link"), bases),
                "description": _field(channel, "description"), "language": _field(channel, "language"),
                "entries": [_rss_entry(node, bases) for node in _children(channel, "item")]}
    if root.tag not in {"feed", _tag(_ATOM, "feed")}:
        raise ValueError("expected an RSS channel or Atom feed")
    entries = []
    authors = _atom_authors(root)
    for node in _children(root, "entry"):
        entries.append({"id": _field(node, "id"), "title": _field(node, "title"),
                        "link": _atom_link(node, bases), "summary": _field(node, "summary"),
                        "content": _field(node, "content"), "published": _field(node, "published"),
                        "updated": _field(node, "updated"), "authors": _atom_authors(node) or list(authors),
                        "categories": [category.get("term", "") for category in _children(node, "category")],
                        "enclosures": _enclosures(node, bases, True)})
    return {"format": "atom", "title": _field(root, "title"), "link": _atom_link(root, bases),
            "description": _field(root, "subtitle"), "language": root.get(_tag(_XML, "lang"), ""), "entries": entries}


__all__ = ["parse_feed", "parse_sitemap"]
