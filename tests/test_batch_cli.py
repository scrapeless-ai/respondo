"""Bounded offline batch journeys; all inputs are synthetic and temporary."""

import csv
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import respondo_batch


class BatchCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.directory = self.base / "inputs"
        self.directory.mkdir()

    def write(self, name, content):
        path = self.directory / name
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return path

    def run_cli(self, mode="text", *options, directory=None):
        return subprocess.run(
            [sys.executable, "-m", "respondo", mode, str(directory or self.directory),
             "--batch", "--format", "jsonl", *options], cwd=ROOT / "src",
            text=True, encoding="utf-8", capture_output=True, timeout=10,
        )

    def rows(self, result, code=0):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_sorted_nonrecursive_outcomes_and_pattern(self):
        self.write("b.html", "<p>Two</p>")
        self.write("a.html", "<h1>One</h1>")
        self.write("skip.txt", "Skip")
        (self.directory / "nested").mkdir()
        (self.directory / "nested" / "c.html").write_text("Not selected")
        rows = self.rows(self.run_cli("text", "--pattern", "*.html"))
        self.assertEqual(rows, [
            {"source": "a.html", "status": "ok", "result": "One", "error": None},
            {"source": "b.html", "status": "ok", "result": "Two", "error": None},
        ])

    def test_scalar_list_empty_and_object_results(self):
        for content, expected in [("null", None), ("4", 4), ("[]", []), ('{"a":1}', {"a": 1})]:
            with self.subTest(content=content):
                self.write("input.json", content)
                row = self.rows(self.run_cli("pointer", "--path", ""))[0]
                self.assertEqual(row["status"], "ok")
                self.assertEqual(row["result"], expected)

    def test_mixed_failure_continues_without_source_disclosure(self):
        self.write("a.json", "SYNTHETIC_PRIVATE_BODY")
        self.write("b.json", '{"ok":1}')
        result = self.run_cli("pointer", "--path", "")
        rows = self.rows(result, 1)
        self.assertEqual(rows[0]["error"], {"code": "invalid_json", "line": 1, "column": 1})
        self.assertEqual(rows[1]["result"], {"ok": 1})
        self.assertNotIn("SYNTHETIC_PRIVATE_BODY", result.stdout + result.stderr)

    def test_invalid_utf8_is_per_file(self):
        self.write("bad", b"\xff")
        self.write("good", "<p>Café</p>")
        rows = self.rows(self.run_cli(), 1)
        self.assertEqual(rows[0]["error"]["code"], "encoding_error")
        self.assertEqual(rows[1]["result"], "Café")

    def test_csv_envelopes_escape_formula_filenames(self):
        self.write("=formula.html", "<p>Café</p>")
        result = self.run_cli("text", "--format", "csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = list(csv.DictReader(io.StringIO(result.stdout)))
        self.assertEqual(list(rows[0]), ["source", "status", "result", "error_code", "error_line", "error_column"])
        self.assertEqual(rows[0]["source"], "'=formula.html")
        self.assertEqual(json.loads(rows[0]["result"]), "Café")
        raw = self.run_cli("text", "--format", "csv", "--raw-csv")
        self.assertEqual(list(csv.DictReader(io.StringIO(raw.stdout)))[0]["source"], "=formula.html")

    def test_empty_selection_and_invalid_directory_fail(self):
        for path in [self.directory, self.directory / "missing", self.write("file", "value")]:
            result = self.run_cli("text", "--pattern", "*.html", directory=path)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_argument_validation(self):
        cases = [("--format", "json"), ("--format", "text"), ("--compact",),
                 ("--pattern", "../*"), ("--pattern", "nested/*"), ("--pattern", ""),
                 ("--max-files", "0"), ("--max-file-bytes", "-1"),
                 ("--max-total-bytes", "no"), ("--max-output-bytes", "0"),
                 ("--max-file-bytes", str(sys.maxsize), "--max-total-bytes", str(sys.maxsize))]
        for options in cases:
            with self.subTest(options=options):
                result = self.run_cli("text", *options)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_file_and_output_count_limits_emit_nothing(self):
        self.write("a", "one")
        self.write("b", "two")
        for options in [("--max-files", "1"), ("--max-total-bytes", "5"), ("--max-output-bytes", "2")]:
            result = self.run_cli("text", *options)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_byte_budget_includes_bom_and_multibyte_text(self):
        self.write("a", "\ufeffé")
        row = self.rows(self.run_cli("text", "--max-file-bytes", "5", "--max-total-bytes", "5"))[0]
        self.assertEqual(row["result"], "é")
        row = self.rows(self.run_cli("text", "--max-file-bytes", "4"), 1)[0]
        self.assertEqual(row["error"]["code"], "file_too_large")

    def test_recipes_are_loaded_and_bounded_before_output(self):
        self.write("a.html", "<article><h2>Tea</h2></article>")
        recipe = self.base / "recipe.json"
        recipe.write_text('{"name":"h2"}')
        row = self.rows(self.run_cli("records", "--selector", "article", "--fields", str(recipe)))[0]
        self.assertEqual(row["result"], [{"name": "Tea"}])
        recipe.write_text("SYNTHETIC_PRIVATE_RECIPE")
        result = self.run_cli("records", "--selector", "article", "--fields", str(recipe))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("SYNTHETIC_PRIVATE", result.stderr)
        recipe.write_bytes(b" " * (1024 * 1024 + 1))
        result = self.run_cli("records", "--selector", "article", "--fields", str(recipe))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_output_is_exclusive_outside_input_and_not_created_on_limit(self):
        self.write("a", "<p>One</p>")
        output = self.base / "out.jsonl"
        result = self.run_cli("text", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        original = output.read_bytes()
        self.assertEqual(json.loads(original)["result"], "One")
        result = self.run_cli("text", "--output", str(output))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(output.read_bytes(), original)
        for destination, options in [(self.directory / "new.jsonl", ()),
                                     (self.base / "limited.jsonl", ("--max-output-bytes", "1"))]:
            result = self.run_cli("text", "--output", str(destination), *options)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(destination.exists())

    def test_selected_symlink_is_error_and_root_symlink_is_rejected(self):
        target = self.write("good", "Value")
        link = self.directory / "link"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("host does not permit symlink creation")
        rows = self.rows(self.run_cli(), 1)
        self.assertEqual(rows[1]["error"]["code"], "unsafe_path")
        root_link = self.base / "linked"
        root_link.symlink_to(self.directory, target_is_directory=True)
        result = self.run_cli(directory=root_link)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO test")
    def test_fifo_never_blocks(self):
        os.mkfifo(self.directory / "pipe")
        row = self.rows(self.run_cli(), 1)[0]
        self.assertEqual(row["error"]["code"], "not_regular_file")

    def test_result_serialization_failure_is_per_file_for_both_formats(self):
        self.write("a.json", '"\\ud800"')
        self.write("b.json", '"good"')
        for format in ("jsonl", "csv"):
            result = self.run_cli("pointer", "--path", "", "--format", format)
            self.assertEqual(result.returncode, 1, result.stderr)
            if format == "jsonl":
                rows = self.rows(result, 1)
                self.assertEqual(rows[0]["error"]["code"], "encoding_error")
                self.assertEqual(rows[1]["result"], "good")
            else:
                rows = list(csv.DictReader(io.StringIO(result.stdout)))
                self.assertEqual(rows[0]["error_code"], "encoding_error")
                self.assertEqual(json.loads(rows[1]["result"]), "good")
        self.write("a.json", '{"a":NaN}')
        self.write("b.json", '{"a":1}')
        rows = self.rows(self.run_cli("json"), 1)
        self.assertEqual(rows[0]["error"]["code"], "invalid_input")
        self.assertEqual(rows[1]["status"], "ok")

    def test_output_alias_containment_uses_directory_identity(self):
        outside = self.base / "alias"
        outside.mkdir()
        with patch.object(respondo_batch.os.path, "samefile", return_value=True):
            with self.assertRaises(respondo_batch.BatchError):
                respondo_batch._output_path(outside / "out.jsonl", self.directory)

    @unittest.skipUnless(os.name == "posix", "POSIX raw filename test")
    def test_non_utf8_filename_is_rejected_before_processing(self):
        raw_name = os.fsencode(self.directory) + b"/bad-\xff"
        with open(raw_name, "wb") as stream:
            stream.write(b"value")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("filename encoding", result.stderr)

    def test_windows_closed_pipe_error_is_not_confused_with_file_error(self):
        reader, writer = os.pipe()
        try:
            output = SimpleNamespace(fileno=lambda: writer)
            with patch.object(respondo_batch.sys, "platform", "win32"):
                self.assertTrue(respondo_batch._closed_pipe(OSError(errno.EINVAL, "synthetic"), output))
                self.assertFalse(respondo_batch._closed_pipe(OSError(errno.EIO, "synthetic"), output))
                with self.write("file", "value").open("rb") as regular:
                    self.assertFalse(respondo_batch._closed_pipe(OSError(errno.EINVAL, "synthetic"), regular))
        finally:
            os.close(reader)
            os.close(writer)

    def test_discovery_limit_counts_unmatched_entries(self):
        for name in ("a", "b", "c.html"):
            self.write(name, "value")
        args = SimpleNamespace(pattern="*.html", max_files=100)
        with patch.object(respondo_batch, "MAX_DIRECTORY_ENTRIES", 2):
            with self.assertRaises(respondo_batch.BatchError) as caught:
                respondo_batch._discover(self.directory, args)
        self.assertEqual(caught.exception.code, "directory_entry_limit")

    def test_changed_file_identity_is_rejected_before_read_and_closed(self):
        target = self.write("target", "value")
        other = self.write("other", "different").stat()
        opened = []
        real_open = os.open

        def capture(*args, **kwargs):
            descriptor = real_open(*args, **kwargs)
            opened.append(descriptor)
            return descriptor

        budget = [100]
        with patch.object(respondo_batch.os, "open", side_effect=capture), patch.object(respondo_batch.os, "fstat", return_value=other):
            with self.assertRaises(respondo_batch.BatchError) as caught:
                respondo_batch._read(target, 100, budget)
        self.assertEqual(caught.exception.code, "unsafe_path")
        self.assertEqual(budget, [100])
        with self.assertRaises(OSError):
            os.fstat(opened[0])

    def test_text_output_copy_handles_split_utf8(self):
        value = "a" * 65535 + "é"
        output = io.StringIO()
        respondo_batch._copy(io.BytesIO(value.encode()), output)
        self.assertEqual(output.getvalue(), value)

    def test_spool_read_error_is_not_mistaken_for_closed_output_pipe(self):
        class BadSpool(io.BytesIO):
            def read(self, size=-1):
                raise OSError(errno.EINVAL, "synthetic spool failure")

        reader, writer = os.pipe()
        try:
            class BadOutput:
                def fileno(self):
                    return writer

                def write(self, value):
                    raise OSError(errno.EINVAL, "synthetic output failure")

            with patch.object(respondo_batch.sys, "platform", "win32"):
                with self.assertRaises(OSError) as caught:
                    respondo_batch._copy(BadSpool(), BadOutput())
                self.assertNotIsInstance(caught.exception, BrokenPipeError)
                with self.assertRaises(BrokenPipeError):
                    respondo_batch._copy(io.BytesIO(b"value"), BadOutput())
        finally:
            os.close(reader)
            os.close(writer)

    def test_recipe_bytes_count_toward_total(self):
        self.write("a.json", "{}")
        recipe = self.base / "patch.json"
        recipe.write_bytes(b"{}")
        result = self.run_cli("merge", "--patch", str(recipe), "--max-total-bytes", "3")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_closed_batch_output_pipe_exits_cleanly(self):
        self.write("a.html", "<p>" + "value " * 10000 + "</p>")
        with subprocess.Popen([sys.executable, "-m", "respondo", "text", str(self.directory),
                               "--batch", "--format", "jsonl"], cwd=ROOT / "src",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            process.stdout.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                self.fail("closed batch output pipe did not exit")
            errors = process.stderr.read()
        self.assertEqual(process.returncode, 0, errors)
        self.assertEqual(errors, b"")


if __name__ == "__main__":
    unittest.main()
