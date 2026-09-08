"""A small explicit CSS selector subset for dependency-free HTML extraction."""

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

from .page import _BLOCKS, _VOID


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
_ATTRIBUTE = re.compile(r'''\[\s*([A-Za-z_][A-Za-z0-9_:-]*)\s*(?:=\s*(?:"([^"\\]*)"|'([^'\\]*)'|([^\s\]"'=<>`\\]+))\s*)?\]''')
_SILENT = {"script", "style", "template", "noscript"}


@dataclass(eq=False)
class _Node:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    parent: Optional["_Node"] = None
    children: List[Any] = field(default_factory=list)


class _Tree(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("")
        self.stack = [self.root]
        self.nodes: List[_Node] = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        # Limited optional-end-tag recovery, not a browser's HTML5 tree builder.
        barriers = {"li": {"ul", "ol"}, "dt": {"dl"}, "dd": {"dl"},
                    "tr": {"table", "tbody", "thead", "tfoot"},
                    "td": {"tr", "table"}, "th": {"tr", "table"},
                    "option": {"select", "datalist"}, "p": {"div", "section", "article"}}
        if tag in barriers:
            peers = {"dt", "dd"} if tag in {"dt", "dd"} else {"td", "th"} if tag in {"td", "th"} else {tag}
            for index in range(len(self.stack) - 1, 0, -1):
                if self.stack[index].tag in barriers[tag]:
                    break
                if self.stack[index].tag in peers:
                    del self.stack[index:]
                    break
        node = _Node(tag, dict((key, value or "") for key, value in attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID:
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _text(node: _Node) -> str:
    ancestor: Optional[_Node] = node
    while ancestor is not None:
        if ancestor.tag in _SILENT:
            return ""
        ancestor = ancestor.parent
    pieces = []
    pending: List[Any] = [node]
    while pending:
        part = pending.pop()
        if isinstance(part, str):
            pieces.append(part)
        elif part.tag not in _SILENT:
            if part.tag in _BLOCKS:
                pieces.append(" ")
                pending.append(" ")
            pending.extend(reversed(part.children))
    return " ".join("".join(pieces).split())


@dataclass
class _Compound:
    tag: str = "*"
    checks: List[tuple] = field(default_factory=list)

    def matches(self, node: _Node) -> bool:
        if not node.tag or (self.tag != "*" and node.tag != self.tag):
            return False
        for kind, name, value in self.checks:
            if kind == "class":
                if name not in node.attrs.get("class", "").split():
                    return False
            elif name not in node.attrs or (value is not None and node.attrs[name] != value):
                return False
        return True


def _compound(selector: str, start: int) -> tuple:
    position = start
    part = _Compound()
    tag = _IDENT.match(selector, position)
    if tag:
        part.tag = tag.group().lower()
        position = tag.end()
    elif position < len(selector) and selector[position] == "*":
        position += 1
    while position < len(selector):
        marker = selector[position]
        if marker in ".#":
            ident = _IDENT.match(selector, position + 1)
            if not ident:
                raise ValueError("invalid class or ID selector")
            part.checks.append(("class", ident.group(), None) if marker == "." else ("attr", "id", ident.group()))
            position = ident.end()
        elif marker == "[":
            attr = _ATTRIBUTE.match(selector, position)
            if not attr:
                raise ValueError("unsupported or invalid attribute selector")
            name, double, single, bare = attr.groups()
            value = next((value for value in (double, single, bare) if value is not None), None)
            part.checks.append(("attr", name.lower(), value))
            position = attr.end()
        else:
            break
    if position == start:
        raise ValueError("expected a tag, class, ID or attribute selector")
    return part, position


def _compile(selector: str) -> list:
    if not isinstance(selector, str):
        raise TypeError("selector must be a string")
    selector = selector.strip()
    if not selector:
        raise ValueError("selector cannot be empty")
    groups = []
    chain = []
    position = 0
    relation = " "
    while position < len(selector):
        part, position = _compound(selector, position)
        chain.append((part, relation))
        if len(chain) > 32:
            raise ValueError("selector chains are limited to 32 components")
        gap = position
        while position < len(selector) and selector[position].isspace():
            position += 1
        if position == len(selector):
            break
        marker = selector[position]
        if marker == ",":
            groups.append(chain)
            chain = []
            relation = " "
            position += 1
        elif marker == ">":
            relation = ">"
            position += 1
        elif position > gap:
            relation = " "
        else:
            raise ValueError("unsupported selector syntax")
        while position < len(selector) and selector[position].isspace():
            position += 1
        if position == len(selector):
            raise ValueError("selector cannot end with a comma or combinator")
    groups.append(chain)
    return groups


def _matches(node: _Node, chain: list, boundary: Optional[_Node]) -> bool:
    # Walk possible ancestor matches so descendant matching can backtrack.
    pending = [(node, len(chain) - 1)]
    visited = set()
    while pending:
        candidate, index = pending.pop()
        state = (candidate, index)
        if state in visited:
            continue
        visited.add(state)
        if not chain[index][0].matches(candidate):
            continue
        if index == 0:
            return True
        if candidate is boundary:
            continue
        parent = candidate.parent
        if chain[index][1] == ">":
            if parent is not None:
                pending.append((parent, index - 1))
        else:
            while parent is not None:
                pending.append((parent, index - 1))
                if parent is boundary:
                    break
                parent = parent.parent
    return False


def _select(nodes: list, groups: list, boundary: Optional[_Node] = None) -> list:
    return [node for node in nodes if any(_matches(node, chain, boundary) for chain in groups)]


def select_html(html: str, selector: str) -> List[Dict[str, Any]]:
    """Return document-order {tag, attrs, text} matches, deduplicating comma groups.

    Supports ASCII tag/*, .class, #id, [attr], [attr=value], descendants, children
    (>) and comma groups. Attribute values may be quoted. No CSS escapes, sibling
    combinators, pseudo-classes or other attribute operators; unsupported syntax
    raises ValueError even for empty HTML. Chains have at most 32 components.

    Text is whitespace-normalized with block boundaries; script/style/template/
    noscript text is omitted. CSS visibility is not evaluated. Attributes are raw
    extracted data, NOT sanitized URLs or safe markup. No JavaScript is executed.
    HTMLParser recovery is limited; this is not a browser/HTML5 DOM implementation.
    """
    groups = _compile(selector)
    return [{"tag": node.tag, "attrs": dict(node.attrs), "text": _text(node)}
            for node in _select(_Tree(html).nodes, groups)]


def _rules(fields: Mapping) -> list:
    if not isinstance(fields, Mapping):
        raise TypeError("fields must be a mapping")
    rules = []
    for name, rule in fields.items():
        if not isinstance(name, str):
            raise TypeError("field names must be strings")
        if isinstance(rule, str):
            rule = {"selector": rule}
        if not isinstance(rule, Mapping):
            raise TypeError("field rules must be selectors or mappings")
        if set(rule) - {"selector", "attr", "many", "default", "required"}:
            raise ValueError("unknown field rule option")
        groups = _compile(rule["selector"]) if "selector" in rule else None
        for key in ("many", "required"):
            if key in rule and not isinstance(rule[key], bool):
                raise TypeError("many and required must be booleans")
        attr = rule.get("attr")
        if "attr" in rule and (not isinstance(attr, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_:-]*", attr)):
            raise ValueError("attr must be a valid ASCII attribute name without whitespace")
        if rule.get("many") and "default" in rule:
            raise ValueError("many fields use [] for missing values; default is scalar-only")
        rules.append((name, groups, attr.lower() if attr else None, rule))
    return rules


def extract_records(html: str, item_selector: str, fields: Mapping) -> List[Dict[str, Any]]:
    """Apply reusable field recipes to repeated HTML items.

    Each field is a selector shorthand or {selector?, attr?, many?, default?,
    required?}. Omit selector to read the item itself; provided selectors search
    descendants only, with ancestry bounded at the item. Read semantic text or
    an attribute. Missing attributes are skipped; empty strings remain values.
    Scalars take the first value or a copied default (None); many fields always
    return lists. Required fields with no values raise ValueError. All recipes
    are validated before parsing, even if no items match. No I/O or coercion.
    """
    groups = _compile(item_selector)
    rules = _rules(fields)
    tree = _Tree(html)
    result = []
    for item in _select(tree.nodes, groups):
        descendants = []
        pending = list(reversed(item.children))
        while pending:
            node = pending.pop()
            if isinstance(node, _Node):
                descendants.append(node)
                pending.extend(reversed(node.children))
        record = {}
        for name, selectors, attr, rule in rules:
            nodes = _select(descendants, selectors, item) if selectors is not None else [item]
            values = [node.attrs[attr] if attr else _text(node) for node in nodes if not attr or attr in node.attrs]
            if rule.get("required") and not values:
                raise ValueError("required field has no matches")
            record[name] = values if rule.get("many") else values[0] if values else copy.deepcopy(rule.get("default"))
        result.append(record)
    return result


__all__ = ["select_html", "extract_records"]
