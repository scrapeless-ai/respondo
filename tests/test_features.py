"""Behavioral coverage for the dependency-free 0.6 extraction tools."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SOURCE))

from respondo import extract_headings, extract_link_details, extract_page, json_query


class JsonQueryTests(unittest.TestCase):
    def setUp(self):
        self.data = {"items": [{"name": "Tea", "price": 3}, {"name": "Coffee", "price": None}, {}]}

    def test_wildcards_preserve_order_and_nulls(self):
        self.assertEqual(json_query(self.data, "$.items[*].name"), ["Tea", "Coffee"])
        self.assertEqual(json_query(self.data, "items[*].price"), [3, None])

    def test_indexes_and_root_arrays(self):
        self.assertEqual(json_query(self.data, "items[0].name"), ["Tea"])
        self.assertEqual(json_query(self.data, "items[-2].name"), ["Coffee"])
        self.assertEqual(json_query([1, 2], "$[-1]"), [2])
        self.assertEqual(json_query([1, 2], "[0]"), [1])

    def test_quoted_keys_are_literal(self):
        data = {"a.b": {"*": {"": {"0": "found"}}}}
        self.assertEqual(json_query(data, "$['a.b'][\"*\"]['']['0']"), ["found"])

    def test_quoted_keys_use_json_escapes(self):
        data = {"a/b": 1, "😀": 2, "it's": 3, 'a"b': 4, "a\\b": 5}
        for path, expected in [
            (r'$["a\/b"]', 1), (r"$['a\/b']", 1),
            (r'$["\ud83d\ude00"]', 2), (r"$['\ud83d\ude00']", 2),
            (r"$['it\'s']", 3), ("$['a\"b']", 4), (r"$['a\\b']", 5),
        ]:
            with self.subTest(path=path):
                self.assertEqual(json_query(data, path), [expected])

    def test_object_and_nested_wildcards(self):
        self.assertEqual(json_query({"a": [1, 2], "b": [3]}, "$.*[*]"), [1, 2, 3])
        self.assertEqual(json_query(self.data, "items[*].*"), ["Tea", 3, "Coffee", None])

    def test_root_preserves_all_json_types(self):
        for data in [None, False, 0, "", [], {}, [1]]:
            for path in ["", "$"]:
                with self.subTest(data=data, path=path):
                    self.assertEqual(json_query(data, path), [data])

    def test_missing_or_incompatible_paths_are_empty(self):
        for path in ["missing", "items[99]", "items[-99]", "items.name", "items[0].name[0]"]:
            with self.subTest(path=path):
                self.assertEqual(json_query(self.data, path), [])
        self.assertEqual(json_query([], "[-1]"), [])
        self.assertEqual(json_query(None, "*"), [])

    def test_invalid_syntax_fails_even_when_data_is_missing(self):
        for path in ["$.", ".name", "$name", "items..name", "[", "[]", "[0:2]", "[?(@.x)]",
                     "items[0]name", "items[+1]", "items[1.0]", 'missing["bad\\q"]', "items ",
                     "missing[__import__('os')]", "items[*]..name"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                json_query({}, path)

    def test_nonstring_path_and_no_mutation(self):
        with self.assertRaises(TypeError):
            json_query(self.data, None)
        before = copy.deepcopy(self.data)
        json_query(self.data, "items[*].name")
        self.assertEqual(self.data, before)


class PageExtractionTests(unittest.TestCase):
    def test_heading_levels_ids_and_inline_spacing(self):
        html = '<h1 id="intro">Hello <em>world</em>!</h1><h3>A<br>B &amp; C</h3><h6>End</h6>'
        self.assertEqual(extract_headings(html), [
            {"level": 1, "id": "intro", "text": "Hello world!"},
            {"level": 3, "id": "", "text": "A B & C"},
            {"level": 6, "id": "", "text": "End"},
        ])

    def test_noncontent_elements_and_comments_are_excluded(self):
        html = ('<head><title>Document</title></head><!-- hidden -->'
                '<template><h1>Hidden</h1><a href="/hidden">Hidden</a></template>'
                '<style>body { color: red }</style><script>const x = 1;</script>'
                '<noscript><h2>Fallback</h2></noscript><h1>Visible</h1>')
        page = extract_page(html)
        self.assertEqual(page["title"], "Document")
        self.assertEqual(page["text"], "Visible")
        self.assertEqual(len(page["headings"]), 1)
        self.assertEqual(page["links"], [])

    def test_omitted_head_end_tag(self):
        html = '<html><head><title>Title</title><body><h1>Heading</h1><a href="/a">Link</a>'
        page = extract_page(html)
        self.assertEqual(page["title"], "Title")
        self.assertEqual(page["text"], "Heading Link")
        self.assertEqual(len(page["headings"]), 1)
        self.assertEqual(len(page["links"]), 1)

    def test_title_without_head_does_not_pollute_body_text(self):
        self.assertEqual(extract_page("<title>Title</title><p>Body</p>")["text"], "Body")

    def test_unclosed_captures_finish_at_parent_boundary(self):
        self.assertEqual(extract_headings("<div><h1>Heading</div><p>Body</p>")[0]["text"], "Heading")
        links = extract_link_details('<div><a href="/a">Link</div><p>Unrelated</p>')
        self.assertEqual(links[0]["text"], "Link")

    def test_unclosed_captures_finish_at_end_of_input(self):
        self.assertEqual(extract_headings("<h2>Last <b>heading")[0]["text"], "Last heading")
        self.assertEqual(extract_link_details('<a href="/a">Last link')[0]["text"], "Last link")

    def test_relative_links_attributes_alt_labels_and_duplicates(self):
        html = ('<a href="../about?a=1&amp;b=2" title="About" rel="NOFOLLOW sponsored">'
                '<img src="icon.svg" alt="Our ">team</a><a href="../about?a=1&amp;b=2">Again</a>')
        links = extract_link_details(html, base="https://example.com/docs/start")
        self.assertEqual(links, [
            {"href": "https://example.com/about?a=1&b=2", "text": "Our team", "title": "About", "rel": ["nofollow", "sponsored"]},
            {"href": "https://example.com/about?a=1&b=2", "text": "Again", "title": "", "rel": []},
        ])

    def test_block_content_inside_anchor_stays_inside_anchor(self):
        link = extract_link_details('<a href="/"><div>First</div><p>Second</p></a>')[0]
        self.assertEqual(link["text"], "First Second")

    def test_unsafe_empty_and_malformed_links_are_omitted(self):
        html = ('<a href="javascript:alert(1)">Bad</a><a href="java\tscript:alert(1)">Bad</a>'
                '<a href="data:text/html,test">Bad</a><a href="ftp://example.com">Bad</a>'
                '<a href="http://[bad">Bad</a><a href=" ">Empty</a><a>No href</a>'
                '<img src="/image.png"><script src="/script.js"></script>'
                '<a href="#section">Section</a>')
        self.assertEqual([link["href"] for link in extract_link_details(html)], ["#section"])

    def test_mail_phone_protocol_relative_links_and_explicit_base(self):
        html = ('<base href="https://ignored.example/"><a href="/docs">Docs</a>'
                '<a href="//cdn.example/file">CDN</a><a href="mailto:hello@example.com">Email</a>'
                '<a href="tel:+1234">Call</a>')
        self.assertEqual([link["href"] for link in extract_link_details(html, "https://example.com")],
                         ["https://example.com/docs", "https://cdn.example/file", "mailto:hello@example.com", "tel:+1234"])

    def test_page_summary_and_empty_shape(self):
        page = extract_page('<title>Shop</title><meta name="description" content="Demo">'
                            '<h1>Catalog</h1><p>Hello <strong>world</strong>!</p>'
                            '<img src="/tea.png"><table><tr><th>Name</th></tr>'
                            '<tr><td>Tea</td></tr></table>', "https://example.com")
        self.assertEqual(page["text"], "Catalog Hello world! Name Tea")
        self.assertEqual(page["meta"]["description"], "Demo")
        self.assertEqual(page["images"][0]["src"], "https://example.com/tea.png")
        self.assertEqual(page["tables"][0]["rows"], [{"Name": "Tea"}])
        self.assertEqual(extract_page(""), {"title": "", "text": "", "meta": {}, "headings": [], "links": [], "images": [], "tables": []})


class CliTests(unittest.TestCase):
    def run_cli(self, *args, content=""):
        return subprocess.run([sys.executable, "-m", "respondo", *args], input=content,
                              text=True, encoding="utf-8", capture_output=True, cwd=SOURCE, timeout=10)

    def test_query_from_stdin(self):
        result = self.run_cli("query", "--path", "$.items[*].name", "--compact",
                              content='{"items":[{"name":"Tea"},{"name":"咖啡"}]}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '["Tea","咖啡"]\n')

    def test_html_modes_from_stdin(self):
        html = '<h1>Heading</h1><p>Text</p><a href="/docs">Docs</a><img src="/img.png">'
        for mode in ["page", "text", "markdown", "links", "headings", "meta", "images", "tables", "json"]:
            with self.subTest(mode=mode):
                result = self.run_cli(mode, "--base", "https://example.com", content=html)
                self.assertEqual(result.returncode, 0, result.stderr)
                json.loads(result.stdout)
        links = json.loads(self.run_cli("links", "--base", "https://example.com", content=html).stdout)
        self.assertEqual(links[0]["href"], "https://example.com/docs")

    def test_plain_text_mode(self):
        result = self.run_cli("text", "--format", "text", content="<p>Hello world</p>")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Hello world\n")

    def test_reads_local_utf8_file_with_bom(self):
        with tempfile.TemporaryDirectory(prefix="respondo-cli-test-") as directory:
            file = Path(directory) / "page.html"
            file.write_text("\ufeff<h2>Café</h2>", encoding="utf-8")
            result = self.run_cli("headings", str(file))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["text"], "Café")

    def test_invalid_json_does_not_echo_input(self):
        result = self.run_cli("query", "--path", "$", content="SYNTHETIC_PRIVATE_CONTENT")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid JSON at line 1", result.stderr)
        self.assertNotIn("SYNTHETIC_PRIVATE_CONTENT", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_paths_report_an_error(self):
        result = self.run_cli("query", "--path", "$..name", content="{}")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_files_and_invalid_utf8(self):
        with tempfile.TemporaryDirectory(prefix="respondo-cli-test-") as directory:
            missing = self.run_cli("page", str(Path(directory) / "missing.html"))
            bad_file = Path(directory) / "invalid.html"
            bad_file.write_bytes(b"\xff\xfe")
            invalid = self.run_cli("page", str(bad_file))
        for result in [missing, invalid]:
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("Traceback", result.stderr)

    def test_argument_errors(self):
        for args in [("query",), ("page", "--path", "$"), ("page", "--format", "text"),
                     ("text", "--format", "text", "--compact"), ("unknown",)]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_invalid_utf8_stdin_and_bom(self):
        result = subprocess.run(
            [sys.executable, "-m", "respondo", "page"], input=b"<p>\xff</p>",
            capture_output=True, cwd=SOURCE, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"encoding error", result.stderr)
        valid = self.run_cli("query", "--path", "$", content="\ufeff[1,2]")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout), [[1, 2]])

    def test_closed_output_pipe_exits_cleanly(self):
        process = subprocess.Popen(
            [sys.executable, "-m", "respondo", "page"], cwd=SOURCE,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        process.stdout.close()
        process.stdout = None
        _, errors = process.communicate(input=b"<p>Hello</p>", timeout=10)
        self.assertEqual(process.returncode, 0, errors)
        self.assertEqual(errors, b"")

    def test_nonfinite_json_is_rejected(self):
        for content in ["NaN", "Infinity", "-Infinity", "1e9999", '{"a": NaN}']:
            with self.subTest(content=content):
                result = self.run_cli("query", "--path", "$", content=content)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)
        embedded = self.run_cli("json", content='prefix {"price": NaN}')
        self.assertEqual(embedded.returncode, 1)
        self.assertEqual(embedded.stdout, "")

    def test_unpaired_surrogates_never_produce_invalid_output(self):
        result = self.run_cli("query", "--path", "$", content='"\\udcff"')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("encoding error", result.stderr)

    def test_help_and_empty_matches(self):
        self.assertEqual(self.run_cli("--help").returncode, 0)
        result = self.run_cli("query", "--path", "missing", content="{}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])


if __name__ == "__main__":
    unittest.main()
