"""Explicit HTTP metadata/decoding tools with no network requests."""

from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import respondo as r


class ResponseToolsTests(unittest.TestCase):
    def test_status_errors_expose_status_not_body(self):
        for status in [400, 404, 429, 500, 599]:
            response = r.Response(status, {}, b"private response body")
            with self.subTest(status=status), self.assertRaises(r.HTTPStatusError) as raised:
                response.raise_for_status()
            self.assertEqual(raised.exception.status, status)
            self.assertIs(raised.exception.response, response)
            self.assertNotIn("private", str(raised.exception))
        for status in [100, 200, 204, 301, 399]:
            response = r.Response(status, {}, b"")
            self.assertIs(response.raise_for_status(), response)

    def test_decode_uses_explicit_encoding_then_header_then_bom(self):
        response = r.Response(200, {"Content-Type": "text/html; charset=windows-1252"}, b"caf\xe9")
        self.assertEqual(response.decode(), "café")
        self.assertEqual(response.decode("latin-1"), "café")
        self.assertEqual(response.text, "caf�")  # Preserve historical property behavior.
        for encoding in ["utf-8-sig", "utf-16", "utf-32"]:
            self.assertEqual(r.Response(200, {}, "café".encode(encoding)).decode(), "café")

    def test_decode_errors_are_explicit(self):
        with self.assertRaises(UnicodeError):
            r.Response(200, {}, b"\xff").decode()
        self.assertEqual(r.Response(200, {}, b"\xff").decode(errors="replace"), "�")
        with self.assertRaises(LookupError):
            r.Response(200, {"content-type": "text/plain; charset=unknown-xyz"}, b"text").decode()

    def test_quoted_content_type_parameters_do_not_override_charset(self):
        response = r.Response(200, {"Content-Type": 'text/plain; note="hello; charset=latin-1"; charset=utf-8'}, "café".encode())
        self.assertEqual(response.content_type(), ("text/plain", "utf-8"))
        self.assertEqual(response.decode(), "café")

    def test_retry_after_seconds_dates_and_invalid_values(self):
        now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
        cases = [("120", 120), ("0", 0), ("Mon, 07 Sep 2026 12:01:00 GMT", 60),
                 ("Mon, 07 Sep 2026 11:00:00 GMT", 0), ("-1", None), ("1.5", None),
                 ("NaN", None), ("bad-date", None), ("", None)]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(r.Response(429, {"Retry-After": value}, b"").retry_after(now=now), expected)
        with self.assertRaises(ValueError):
            r.Response(429, {}, b"").retry_after(now=datetime(2026, 1, 1))

    def test_retry_after_rejects_trailing_garbage_and_controls(self):
        now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
        for suffix in [" garbage", "\r\nInjected: x", "\n"]:
            self.assertIsNone(r.Response(429, {"Retry-After": "Mon, 07 Sep 2026 12:01:00 GMT" + suffix}, b"").retry_after(now=now))
        for value in ["Monday, 07-Sep-26 12:01:00 GMT", "Mon Sep  7 12:01:00 2026"]:
            self.assertEqual(r.Response(429, {"Retry-After": value}, b"").retry_after(now=now), 60)

    def test_link_headers_resolve_urls_and_preserve_parameters(self):
        response = r.Response(200, {}, b"", raw_headers=[
            ("Link", '</items?page=2>; rel="next last"; title="two, three; four", </items?page=1>; rel=prev'),
            ("link", '<https://example.test/a,b>; rel=related; title="a\\\"b"'),
        ])
        self.assertEqual(response.links(base="https://example.test/"), [
            {"url": "https://example.test/items?page=2", "rel": ["next", "last"], "params": {"rel": "next last", "title": "two, three; four"}},
            {"url": "https://example.test/items?page=1", "rel": ["prev"], "params": {"rel": "prev"}},
            {"url": "https://example.test/a,b", "rel": ["related"], "params": {"rel": "related", "title": 'a"b'}},
        ])
        self.assertEqual(r.Response(200, {}, b"").links(), [])

    def test_valueless_link_extensions_are_preserved(self):
        self.assertEqual(r.Response(200, {"Link": '</next>; rel=next; customflag'}, b"").links()[0]["params"],
                         {"rel": "next", "customflag": ""})

    def test_link_duplicate_parameters_keep_first_and_bad_syntax_fails(self):
        value = '<a>; rel=next; rel=prev; title*=UTF-8\'\'hello'
        link = r.Response(200, {"Link": value}, b"").links()[0]
        self.assertEqual(link["rel"], ["next"])
        self.assertEqual(link["params"]["title*"], "UTF-8''hello")
        for value in ['broken', '<a>; rel="bad', '<a> trailing', '<a>; =bad', '<a>\r\nInjected: x']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.Response(200, {"Link": value}, b"").links()

    def test_extraction_methods_use_decoded_text_and_json_queries(self):
        response = r.Response(200, {"Content-Type": "text/html; charset=latin-1"}, b'<article><h2>Caf\xe9</h2></article>')
        self.assertEqual(response.select_html("h2")[0]["text"], "Café")
        self.assertEqual(response.extract_records("article", {"name": "h2"}), [{"name": "Café"}])
        self.assertEqual(response.extract_page()["headings"][0]["text"], "Café")
        self.assertEqual(r.Response(200, {}, b'{"items":[1,2]}').json_query("$.items[*]"), [1, 2])


if __name__ == "__main__":
    unittest.main()
