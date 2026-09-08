"""Public selector subset and repeated-record extraction contracts."""

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import respondo as r


HTML = '''<main id="catalog"><article class="card featured" data-id="a">
  <h2>Green <em>tea</em></h2><a href="/tea">Details</a><b class="price">3</b>
  <span class="tag">Hot</span><span class="tag">Organic</span>
</article><article class="card" data-id="b"><h2>Coffee</h2></article></main>'''


class SelectorTests(unittest.TestCase):
    def test_tag_id_class_and_attributes(self):
        cases = [("article", 2), ("#catalog", 1), (".card.featured", 1),
                 ("article[data-id]", 2), ('[data-id="a"]', 1), ("[data-id=b]", 1),
                 ("ARTICLE.card", 2), (".missing", 0)]
        for selector, count in cases:
            with self.subTest(selector=selector):
                self.assertEqual(len(r.select_html(HTML, selector)), count)

    def test_result_shape_and_semantic_text(self):
        self.assertEqual(r.select_html('<p ID="x" disabled>A<b>B</b><br>C &amp; D<script>secret</script></p>', "p"),
                         [{"tag": "p", "attrs": {"id": "x", "disabled": ""}, "text": "AB C & D"}])
        self.assertEqual(r.select_html("<title>A title</title>", "title")[0]["text"], "A title")

    def test_child_descendant_and_group_order(self):
        self.assertEqual([x["text"] for x in r.select_html(HTML, "main > article h2")], ["Green tea", "Coffee"])
        self.assertEqual(r.select_html(HTML, "main > h2"), [])
        self.assertEqual([x["text"] for x in r.select_html(HTML, "article h2, #catalog h2, h2")], ["Green tea", "Coffee"])
        self.assertEqual([x["tag"] for x in r.select_html("<div><p>A</p></div>", "p, div")], ["div", "p"])

    def test_quoted_punctuation_is_not_a_combinator(self):
        html = '<a title="x, y > z" data-tag="a.b">yes</a>'
        self.assertEqual(r.select_html(html, '[title="x, y > z"][data-tag=\'a.b\']')[0]["text"], "yes")

    def test_ancestry_backtracks_and_does_not_cross_siblings(self):
        html = '<a><b><b><c>yes</c></b></b></a><c>no</c>'
        self.assertEqual([x["text"] for x in r.select_html(html, "a > b c")], ["yes"])
        self.assertEqual(r.select_html("<a></a><b>x</b>", "a b"), [])

    def test_void_self_closing_and_omitted_list_end_tags(self):
        self.assertEqual([x["text"] for x in r.select_html("<ul><li>A<li>B</ul>", "ul > li")], ["A", "B"])
        self.assertEqual(len(r.select_html("<div><img src='a'><br><custom/><span>x</span></div>", "div > *")), 4)
        html = '<ul><li>A<ul><li>B</li></ul></li><li>C</li></ul>'
        self.assertEqual(len(r.select_html(html, "ul > li")), 3)

    def test_invalid_or_unsupported_syntax_fails_on_empty_document(self):
        for selector in ["", " ", "div,", ",div", "div + p", "div ~ p", ":first-child", "div:hover",
                         "div[", "[x^=y]", "div >", "> div", "div >> p", "[x='a]", "div..a"]:
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                r.select_html("", selector)
        with self.assertRaises(TypeError):
            r.select_html("", None)

    def test_output_does_not_share_mutable_attributes(self):
        matches = r.select_html(HTML, "article")
        matches[0]["attrs"]["data-id"] = "changed"
        self.assertEqual(r.select_html(HTML, "article")[0]["attrs"]["data-id"], "a")

    def test_selected_template_descendants_have_no_content_text(self):
        html = '<template><p>Hidden</p></template><p>Visible</p>'
        self.assertEqual([x["text"] for x in r.select_html(html, "p")], ["", "Visible"])

    def test_descendant_matching_does_not_revisit_identical_states(self):
        from htmlparse.selectors import _Compound
        original = _Compound.matches
        calls = []

        def counted(compound, node):
            calls.append(1)
            return original(compound, node)

        html = "<div>" * 20 + "x" + "</div>" * 20
        with patch.object(_Compound, "matches", counted):
            self.assertEqual(r.select_html(html, "missing " + "div " * 8), [])
        self.assertLess(len(calls), 20 * 21 * 9)


class RecordTests(unittest.TestCase):
    def test_repeated_cards_with_scalar_many_and_defaults(self):
        fields = {"name": "h2", "url": {"selector": "a", "attr": "href"},
                  "tags": {"selector": ".tag", "many": True},
                  "price": {"selector": ".price", "default": "n/a"},
                  "id": {"attr": "data-id"}}
        self.assertEqual(r.extract_records(HTML, "article", fields), [
            {"name": "Green tea", "url": "/tea", "tags": ["Hot", "Organic"], "price": "3", "id": "a"},
            {"name": "Coffee", "url": None, "tags": [], "price": "n/a", "id": "b"},
        ])

    def test_scoped_selectors_cannot_use_outside_ancestors(self):
        fields = {"name": "main h2", "other": "article h2", "own": {}}
        rows = r.extract_records(HTML, "article", fields)
        self.assertIsNone(rows[0]["name"])
        self.assertEqual(rows[0]["other"], "Green tea")
        self.assertIn("Green tea", rows[0]["own"])

    def test_missing_attributes_are_skipped_but_empty_values_retained(self):
        html = '<div><a>missing</a><a href="">empty</a><a href="/x">x</a></div>'
        rows = r.extract_records(html, "div", {"first": {"selector": "a", "attr": "href"},
                                              "all": {"selector": "a", "attr": "href", "many": True}})
        self.assertEqual(rows, [{"first": "", "all": ["", "/x"]}])

    def test_required_and_mutable_defaults(self):
        with self.assertRaisesRegex(ValueError, "required field"):
            r.extract_records(HTML, "article", {"price": {"selector": ".price", "required": True}})
        rows = r.extract_records(HTML, "article", {"missing": {"selector": "aside", "default": []}})
        rows[0]["missing"].append(1)
        self.assertEqual(rows[1]["missing"], [])

    def test_rule_validation_runs_without_items(self):
        rules = [{"x": {"seletor": "p"}}, {"x": {"selector": "p:hover"}},
                 {"x": {"many": "yes"}}, {"x": {"required": 1}},
                 {"x": {"attr": ""}}, {"x": {"attr": " data-id "}}, {"x": {"many": True, "default": 1}},
                 {"x": 9}, {1: "p"}]
        for fields in rules:
            with self.subTest(fields=fields), self.assertRaises((ValueError, TypeError)):
                r.extract_records("", "article", fields)
        self.assertEqual(r.extract_records("", "article", {"x": "p"}), [])


if __name__ == "__main__":
    unittest.main()
