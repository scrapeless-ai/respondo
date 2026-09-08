"""End-to-end CLI journeys using synthetic documents and temporary recipe files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class PipelineCliTests(unittest.TestCase):
    def test_cli_round_trip_ignores_non_utf8_host_default(self):
        with patch.object(subprocess, "_text_encoding", return_value="cp1252", create=True):
            result = self.run_cli("text", content="<h1>咖啡</h1>")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), "咖啡")

    def run_cli(self, *args, content=""):
        return subprocess.run([sys.executable, "-m", "respondo", *args], cwd=ROOT / "src",
                              input=content, text=True, encoding="utf-8", capture_output=True, timeout=10)

    def test_version_and_help_cover_new_modes(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0.6.0", result.stdout)
        self.assertIn("records", self.run_cli("--help").stdout)

    def test_select_and_records_with_recipe_file(self):
        html = '<article><h2>Tea</h2><a href="/tea">Details</a></article>'
        result = self.run_cli("select", "--selector", "h2", content=html)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["text"], "Tea")
        with tempfile.TemporaryDirectory() as directory:
            fields = Path(directory) / "fields.json"
            fields.write_text(json.dumps({"name": "h2", "url": {"selector": "a", "attr": "href"}}))
            result = self.run_cli("records", "--selector", "article", "--fields", str(fields), "--format", "jsonl", content=html)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"name": "Tea", "url": "/tea"})

    def test_pointer_flatten_and_merge(self):
        result = self.run_cli("pointer", "--path", "/a~1b/0", content='{"a/b":[3]}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), 3)
        result = self.run_cli("flatten", content='{"a":[3]}')
        self.assertEqual(json.loads(result.stdout), {"/a/0": 3})
        with tempfile.TemporaryDirectory() as directory:
            patch = Path(directory) / "patch.json"
            patch.write_text('{"a":null,"b":2}')
            result = self.run_cli("merge", "--patch", str(patch), content='{"a":1}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"b": 2})

    def test_project_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            fields = Path(directory) / "columns.json"
            fields.write_text('{"label":"/name","cost":"/price"}')
            result = self.run_cli("project", "--fields", str(fields), "--format", "csv", content='[{"name":"Tea","price":3}]')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "label,cost\nTea,3\n")

    def test_jsonl_and_csv_import_and_export(self):
        result = self.run_cli("jsonl", "--skip-blank", "--format", "csv", content='{"a":1}\n\n{"a":2}\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "a\n1\n2\n")
        result = self.run_cli("csv", "--delimiter", ";", "--format", "jsonl", content="name;price\nTea;3\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"name": "Tea", "price": "3"})

    def test_csv_formula_escaping_and_raw_opt_in(self):
        content = '[{"name":"=1+1"}]'
        safe = self.run_cli("query", "--path", "$[*]", "--format", "csv", content=content)
        raw = self.run_cli("query", "--path", "$[*]", "--format", "csv", "--raw-csv", content=content)
        self.assertEqual(safe.returncode, 0, safe.stderr)
        self.assertIn("'=1+1", safe.stdout)
        self.assertNotIn("'=1+1", raw.stdout)

    def test_feed_sitemap_and_url(self):
        result = self.run_cli("feed", content="<rss><channel><title>News</title></channel></rss>")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["title"], "News")
        result = self.run_cli("sitemap", content="<urlset/>")
        self.assertEqual(json.loads(result.stdout), {"type": "urlset", "entries": []})
        result = self.run_cli("url", "--remove-tracking", "--drop-fragment", "--format", "text",
                              content="HTTPS://EXAMPLE.TEST/?utm_source=x&a=1#part\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "https://example.test/?a=1\n")

    def test_missing_options_and_irrelevant_options_exit_two(self):
        cases = [("select",), ("records", "--selector", "a"), ("project",), ("merge",),
                 ("pointer",), ("text", "--selector", "a"), ("text", "--fields", "x"),
                 ("text", "--skip-blank"), ("text", "--remove-tracking"),
                 ("query", "--path", "$", "--format", "jsonl", "--compact"),
                 ("text", "--raw-csv"), ("text", "--format", "csv")]
        for args in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_data_errors_are_nonzero_without_partial_results_or_tracebacks(self):
        cases = [("pointer", "--path", "/missing", "{}"),
                 ("jsonl", '{"ok":1}\nnot-json'), ("feed", "<feed>"),
                 ("url", "ftp://example.test"), ("csv", "a,b\n1"),
                 ("query", "--path", "$[*]", "--format", "csv", "[1,2]")]
        for *args, content in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args, content=content)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn("not-json", result.stderr)

    def test_url_parser_errors_do_not_echo_source_values(self):
        marker = "SYNTHETIC_PRIVATE"
        url = "https://" + marker + "@／example.test/"
        for mode, content in [("feed", '<feed><link href="' + url + '"/></feed>'),
                              ("images", '<img src="' + url + '">'), ("page", '<img src="' + url + '">')]:
            result = self.run_cli(mode, "--base", "https://example.test/", content=content)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertNotIn(marker, result.stderr)

    def test_projection_requires_a_json_array_even_when_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            fields = Path(directory) / "fields.json"
            fields.write_text('{"a":"/a"}')
            for content in ["{}", '""', 'null', "1"]:
                result = self.run_cli("project", "--fields", str(fields), content=content)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
