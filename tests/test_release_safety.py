"""Regression tests for inherited release blockers, with synthetic credentials."""

import sys
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ai
import respondo


class ReleaseSafetyTests(unittest.TestCase):
    def test_gemini_authentication_is_a_header_not_a_url(self):
        with patch.object(ai, "_http_post", return_value="ok") as post:
            self.assertEqual(ai._call_gemini("extract", "synthetic", "test-only-not-a-credential", "gemini-example", None), "ok")
        url, headers, payload, path = post.call_args.args
        self.assertNotIn("test-only-not-a-credential", url)
        self.assertNotIn("?key=", url)
        self.assertEqual(headers["x-goog-api-key"], "test-only-not-a-credential")

    def test_gemini_model_cannot_change_url_structure(self):
        with patch.object(ai, "_http_post", return_value="ok") as post:
            ai._call_gemini("extract", "synthetic", "test-only", "model?other=1", None)
        self.assertNotIn("?", post.call_args.args[0])

    def test_public_exports_resolve(self):
        self.assertFalse([name for name in respondo.__all__ if not hasattr(respondo, name)])
        self.assertEqual(len(respondo.__all__), len(set(respondo.__all__)))

    def test_legacy_runner_fails_closed_and_reports_counts(self):
        from scripts.run_tests import run_legacy
        for status, passed, failed, expected in [(0, 5, 0, True), (0, 0, 0, False),
                                                  (1, 5, 0, False), (0, 5, 1, False)]:
            module = SimpleNamespace(__name__="synthetic", main=lambda: status, passed=passed, failed=failed)
            with self.subTest(status=status, passed=passed, failed=failed), redirect_stdout(io.StringIO()):
                self.assertEqual(run_legacy(module), expected)


if __name__ == "__main__":
    unittest.main()
